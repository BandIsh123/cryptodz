from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from eth_abi import encode as abi_encode
from eth_account import Account
from eth_utils import keccak
from hexbytes import HexBytes
from web3 import Web3

from .client import AsyncEvmClient
from .utils import to_wei
from .tokens import USDC_E, balance_of, allowance, encode_approve


@dataclass
class SyncSwapTemplate:
    tx_hash: str  #


class SyncSwap:


    TEMPLATE_SELECTOR = bytes.fromhex("0ae6a646")

    PERMIT_TYPEHASH = keccak(
        text="Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)"
    )

    def __init__(self, client: AsyncEvmClient, template: SyncSwapTemplate):
        self.client = client
        self.template = template

    def _w3(self) -> Web3:
        return self.client._require_w3()

    @staticmethod
    def _to_bytes(x: Any) -> bytes:
        if isinstance(x, (bytes, bytearray)):
            return bytes(x)
        if isinstance(x, HexBytes):
            return bytes(x)
        if hasattr(x, "hex"):
            hx = x.hex()
            if isinstance(hx, str):
                if hx.startswith("0x"):
                    hx = hx[2:]
                return bytes.fromhex(hx)
        s = str(x)
        if s.startswith("0x"):
            s = s[2:]
        return bytes.fromhex(s)

    @staticmethod
    def _read_u256(buf: bytes, off: int) -> int:
        return int.from_bytes(buf[off : off + 32], "big")

    @staticmethod
    def _write_u256(buf: bytearray, off: int, val: int) -> None:
        buf[off : off + 32] = int(val).to_bytes(32, "big")

    async def _load_template(self) -> tuple[str, bytes]:
        tx = await self.client.get_tx(self.template.tx_hash)
        to_addr = tx.get("to")
        if not to_addr:
            raise RuntimeError("Template tx has no 'to' address")
        input_data = tx.get("input")
        if input_data is None:
            raise RuntimeError("Template tx has no 'input' field")

        router_addr = Web3.to_checksum_address(to_addr)
        calldata = self._to_bytes(input_data)
        if len(calldata) < 4 + 32:
            raise RuntimeError("Template input too short")
        return router_addr, calldata

    def _extract_paths_blob_from_template(self, template_calldata: bytes) -> bytes:

        sel = template_calldata[:4]
        if sel != self.TEMPLATE_SELECTOR:
            raise RuntimeError(f"Unexpected template selector: 0x{sel.hex()}")

        data = template_calldata[4:]
        paths_off = self._read_u256(data, 0)
        if paths_off % 32 != 0 or paths_off >= len(data):
            raise RuntimeError(f"Bad paths_off={paths_off}")
        return data[paths_off:]

    def _patch_amount_in_paths(self, paths_blob: bytes, new_amount_in: int) -> tuple[bytes, str, int]:

        b = bytearray(paths_blob)

        paths_len = self._read_u256(b, 0)
        if paths_len != 1:
            raise RuntimeError(f"Unsupported paths_len={paths_len} (expected 1)")

        off0 = self._read_u256(b, 32)
        el0 = 32 + off0

        token_word = self._read_u256(b, el0 + 32)
        token_in = Web3.to_checksum_address("0x" + token_word.to_bytes(32, "big")[-20:].hex())

        amount_off = el0 + 64
        old_amount = self._read_u256(b, amount_off)
        self._write_u256(b, amount_off, int(new_amount_in))

        return bytes(b), token_in, int(old_amount)

    def _erc20_permit_contract(self, token: str):

        w3 = self._w3()
        abi = [
            {
                "name": "nonces",
                "type": "function",
                "stateMutability": "view",
                "inputs": [{"type": "address", "name": "owner"}],
                "outputs": [{"type": "uint256"}],
            },
            {
                "name": "DOMAIN_SEPARATOR",
                "type": "function",
                "stateMutability": "view",
                "inputs": [],
                "outputs": [{"type": "bytes32"}],
            },
        ]
        return w3.eth.contract(address=Web3.to_checksum_address(token), abi=abi)

    def _sign_permit(
        self,
        token: str,
        owner: str,
        spender: str,
        value: int,
        deadline: int,
        private_key: str,
    ) -> Tuple[int, bytes, bytes]:

        c = self._erc20_permit_contract(token)

        owner = Web3.to_checksum_address(owner)
        spender = Web3.to_checksum_address(spender)

        nonce = c.functions.nonces(owner).call()
        domain_separator = c.functions.DOMAIN_SEPARATOR().call()

        encoded = abi_encode(
            ["bytes32", "address", "address", "uint256", "uint256", "uint256"],
            [self.PERMIT_TYPEHASH, owner, spender, int(value), int(nonce), int(deadline)],
        )
        struct_hash = keccak(encoded)
        digest = keccak(b"\x19\x01" + domain_separator + struct_hash)

        if hasattr(Account, "signHash"):
            signed = Account.signHash(digest, private_key=private_key)
        else:
            signed = Account._sign_hash(digest, private_key=private_key)

        v = signed.v
        r = int(signed.r).to_bytes(32, "big")
        s = int(signed.s).to_bytes(32, "big")
        return v, r, s

    def _encode_swap_with_permit_calldata(
        self,
        paths_blob: bytes,
        amount_out_min: int,
        swap_deadline: int,
        permit_token: str,
        permit_value: int,
        permit_deadline: int,
        v: int,
        r: bytes,
        s: bytes,
        eth_unwrap_recipient: str,
    ) -> bytes:

        head = bytearray()
        head += (0x140).to_bytes(32, "big")
        head += int(amount_out_min).to_bytes(32, "big")
        head += int(swap_deadline).to_bytes(32, "big")

        head += int(Web3.to_checksum_address(permit_token), 16).to_bytes(32, "big")
        head += int(permit_value).to_bytes(32, "big")
        head += int(permit_deadline).to_bytes(32, "big")
        head += int(v).to_bytes(32, "big")
        head += r.ljust(32, b"\x00")
        head += s.ljust(32, b"\x00")

        head += int(Web3.to_checksum_address(eth_unwrap_recipient), 16).to_bytes(32, "big")

        return self.TEMPLATE_SELECTOR + bytes(head) + paths_blob

    async def swap_usdc_e_to_eth(self, usdc_amount: Optional[str], slippage: float, is_all_balance: bool = False) -> str:
        w3 = self._w3()

        router_addr, template_calldata = await self._load_template()

        # amountIn
        if is_all_balance:
            amount_in = balance_of(w3, USDC_E, self.client.address)
        else:
            if usdc_amount is None:
                raise ValueError("Set --amount or use --all")
            amount_in = to_wei(usdc_amount, 6)

        if amount_in <= 0:
            raise ValueError("amount_in is 0")

        bal = balance_of(w3, USDC_E, self.client.address)
        print(f"USDC.e balance={bal} need={amount_in}")
        if bal < amount_in:
            raise ValueError(f"Not enough USDC.e balance: have={bal}, need={amount_in}")

        # approve
        cur_allow = allowance(w3, USDC_E, self.client.address, router_addr)
        if cur_allow < amount_in:
            print("Approve USDC.e -> SyncSwap router (optional) ...")
            approve_data = encode_approve(w3, USDC_E, router_addr, 2**256 - 1)
            txa = await self.client.sign_and_send(to=USDC_E, data=approve_data, value=0)
            await self.client.wait_receipt(txa)


        paths_blob = self._extract_paths_blob_from_template(template_calldata)
        patched_paths, token_in, old_amount = self._patch_amount_in_paths(paths_blob, amount_in)
        print(f"[template] tokenIn={token_in} old_amountIn={old_amount} -> new_amountIn={amount_in}")

        now = int(time.time())
        swap_deadline = now + 900
        permit_deadline = now + 3600


        amount_out_min = 1

        # private key
        pk = getattr(self.client, "private_key", None) or getattr(self.client, "_private_key", None)
        if not pk:
            raise RuntimeError("Cannot access private key on client to sign permit")

        # SIGN permit for USDC.e
        v, r, s = self._sign_permit(
            token=USDC_E,
            owner=self.client.address,
            spender=router_addr,
            value=amount_in,
            deadline=permit_deadline,
            private_key=pk,
        )


        eth_unwrap_recipient = "0x0000000000000000000000000000000000000000"

        calldata = self._encode_swap_with_permit_calldata(
            paths_blob=patched_paths,
            amount_out_min=amount_out_min,
            swap_deadline=swap_deadline,
            permit_token=USDC_E,
            permit_value=amount_in,
            permit_deadline=permit_deadline,
            v=v, r=r, s=s,
            eth_unwrap_recipient=eth_unwrap_recipient,
        )

        print(
            "SyncSwap SWAP_WITH_PERMIT USDC.e->ETH\n"
            f"  amount_in={amount_in} min={amount_out_min} slippage={slippage} all={is_all_balance}\n"
            f"  router={router_addr} permit_deadline={permit_deadline} swap_deadline={swap_deadline}"
        )

        return await self.client.sign_and_send(to=router_addr, data=calldata, value=0)
