from __future__ import annotations

from dataclasses import dataclass
from web3 import Web3

from .client import AsyncEvmClient
from .utils import to_wei
from .tokens import USDC_E, balance_of, allowance, encode_approve
from hexbytes import HexBytes

def _to_hexstr(x) -> str:

    if isinstance(x, str):
        return x
    if isinstance(x, (bytes, bytearray, HexBytes)):
        return "0x" + bytes(x).hex()
    raise TypeError(f"Unsupported type for calldata: {type(x)}")


def _strip_0x(x) -> str:

    s = _to_hexstr(x)
    return s[2:] if s.startswith("0x") else s


@dataclass
class MaverickTemplate:
    tx_hash: str

    template_amount_in: int = 10

def _word32(n: int) -> str:
    return hex(int(n))[2:].rjust(64, "0")


def _replace_word_once(calldata_hex: str, old_word_64: str, new_word_64: str) -> str:

    x = _strip_0x(calldata_hex).lower()
    old_word_64 = old_word_64.lower()
    new_word_64 = new_word_64.lower()

    idx = x.find(old_word_64)
    if idx == -1:
        raise RuntimeError("amountIn word not found in template calldata (anchor mismatch).")

    if x.find(old_word_64, idx + 1) != -1:
        raise RuntimeError("amountIn word found multiple times in calldata. Need a more specific anchor.")
    x2 = x[:idx] + new_word_64 + x[idx + 64 :]
    return "0x" + x2


class Maverick:


    def __init__(self, client: AsyncEvmClient, template: MaverickTemplate):
        self.client = client
        self.template = template

    def _w3(self) -> Web3:
        return self.client._require_w3()

    async def _load_template_tx(self) -> tuple[str, str]:
        tx = await self.client.get_tx(self.template.tx_hash)
        to_addr = tx.get("to")
        data = tx.get("input") or tx.get("data")
        if not to_addr or not data:
            raise RuntimeError("Template tx has empty 'to' or 'input'.")
        return (to_addr, data)

    async def _ensure_approve(self, spender: str, need_amount: int):
        w3 = self._w3()
        cur = allowance(w3, USDC_E, self.client.address, spender)
        if cur >= need_amount:
            return
        print("Approve USDC.e -> Maverick router ...")
        approve_data = encode_approve(w3, USDC_E, spender, 2**256 - 1)
        txa = await self.client.sign_and_send(to=USDC_E, data=approve_data, value=0)
        await self.client.wait_receipt(txa)

    async def usdc_e_swap_from_template(self, usdc_amount: str | None, slippage: float, is_all_balance: bool = False) -> str:
        w3 = self._w3()

        to_addr, input_data = await self._load_template_tx()
        router = w3.to_checksum_address(to_addr)

        if is_all_balance:
            amount_in = balance_of(w3, USDC_E, self.client.address)
        else:
            if usdc_amount is None:
                raise ValueError("Set --amount or use --all")
            amount_in = to_wei(usdc_amount, 6)

        if amount_in <= 0:
            raise ValueError("amount_in is 0")

        # approve
        await self._ensure_approve(router, amount_in)


        old_word = _word32(self.template.template_amount_in)
        new_word = _word32(amount_in)

        new_data = _replace_word_once(input_data, old_word, new_word)

        print(f"Maverick TEMPLATE SWAP amount_in={amount_in} (old={self.template.template_amount_in}) router={router}")
        # slippage

        return await self.client.sign_and_send(to=router, data=new_data, value=0)
