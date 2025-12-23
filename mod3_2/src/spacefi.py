from __future__ import annotations
from .tokens import USDT, USDC_E, balance_of, encode_approve, allowance

import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from web3 import Web3

from .client import AsyncEvmClient
from .tokens import balance_of, allowance, encode_approve

# SpaceFi Swap
SPACEFI_ROUTER = "0xbE7D1Fd1F6748BBDefC4fbaCafBb11C6Fc506d1D"  # DEX router

# Tokens (zkSync Era)
WETH = "0x5aea5775959fbc2557cc8789bc1bf90a239d9a91"
USDT = "0x493257fD37EDB34451f62EDf8D2a0C418852bA4C"
USDC_E = "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4"

ROUTER_ABI = [
    {
        "name": "getAmountsOut",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"type": "uint256", "name": "amountIn"},
            {"type": "address[]", "name": "path"},
        ],
        "outputs": [{"type": "uint256[]", "name": "amounts"}],
    },
    {
        "name": "swapExactETHForTokens",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [
            {"type": "uint256", "name": "amountOutMin"},
            {"type": "address[]", "name": "path"},
            {"type": "address", "name": "to"},
            {"type": "uint256", "name": "deadline"},
        ],
        "outputs": [{"type": "uint256[]", "name": "amounts"}],
    },
    {
        "name": "swapExactTokensForETH",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"type": "uint256", "name": "amountIn"},
            {"type": "uint256", "name": "amountOutMin"},
            {"type": "address[]", "name": "path"},
            {"type": "address", "name": "to"},
            {"type": "uint256", "name": "deadline"},
        ],
        "outputs": [{"type": "uint256[]", "name": "amounts"}],
    },
    {
        "name": "swapExactTokensForTokens",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"type": "uint256", "name": "amountIn"},
            {"type": "uint256", "name": "amountOutMin"},
            {"type": "address[]", "name": "path"},
            {"type": "address", "name": "to"},
            {"type": "uint256", "name": "deadline"},
        ],
        "outputs": [{"type": "uint256[]", "name": "amounts"}],
    },
]


def to_wei(amount: str, decimals: int) -> int:

    try:
        d = Decimal(amount)
    except (InvalidOperation, TypeError):
        raise ValueError(f"Bad amount: {amount!r}")
    if d <= 0:
        raise ValueError("Amount must be > 0")

    scale = Decimal(10) ** decimals
    return int(d * scale)


@dataclass
class TokenAmount:
    token: str
    amount: str


class SpaceFi:
    def __init__(self, client: AsyncEvmClient):
        self.client = client

    def _w3(self) -> Web3:
        return self.client._require_w3()

    def _router(self):
        w3 = self._w3()
        router_addr = w3.to_checksum_address(SPACEFI_ROUTER)

        # быстрый sanity-check
        code = w3.eth.get_code(router_addr)
        if len(code) == 0:
            raise RuntimeError(
                f"SpaceFi router has no code at {router_addr}. "
                f"Check that you are on zkSync Era RPC (chainId=324)."
            )

        return w3.eth.contract(address=router_addr, abi=ROUTER_ABI)

    def _min_out(self, amount_in_wei: int, path: list[str], slippage: float) -> int:
        w3 = self._w3()
        router = self._router()

        amounts = router.functions.getAmountsOut(
            int(amount_in_wei),
            [w3.to_checksum_address(x) for x in path],
        ).call()

        out = int(amounts[-1])
        # slippage=1 => 1%
        return int(out * (100 - float(slippage)) / 100)

    async def eth_to_usdt(self, eth_amount: str, slippage: float = 1.0) -> str:

        w3 = self._w3()
        router = self._router()

        amount_in = to_wei(eth_amount, 18)
        path = [WETH, USDT]
        out_min = self._min_out(amount_in, path, slippage)
        deadline = int(time.time()) + 600

        data = router.encode_abi(
            "swapExactETHForTokens",
            args=[
                int(out_min),
                [w3.to_checksum_address(x) for x in path],
                w3.to_checksum_address(self.client.address),
                int(deadline),
            ],
        )

        print(f"SpaceFi SWAP: ETH -> USDT | value={amount_in} | out_min={out_min} | slippage={slippage}%")
        return await self.client.sign_and_send(to=SPACEFI_ROUTER, data=data, value=amount_in)

    async def usdc_e_to_eth(self, usdc_amount: str | None, slippage: float = 1.0, is_all_balance: bool = False) -> str:

        w3 = self._w3()
        router = self._router()

        if is_all_balance:
            amount_in = int(balance_of(w3, USDC_E, self.client.address))
        else:
            if usdc_amount is None:
                raise ValueError("Provide --amount or use --all")
            amount_in = to_wei(usdc_amount, 6)

        if amount_in <= 0:
            raise ValueError("Amount is zero")

        # approve
        cur_allow = int(allowance(w3, USDC_E, self.client.address, SPACEFI_ROUTER))
        if cur_allow < amount_in:
            print("Approve USDC.e -> SpaceFi router ...")
            approve_data = encode_approve(w3, USDC_E, SPACEFI_ROUTER, 2**256 - 1)
            txa = await self.client.sign_and_send(to=USDC_E, data=approve_data, value=0)
            await self.client.wait_receipt(txa)

        path = [USDC_E, WETH]
        out_min = self._min_out(amount_in, path, slippage)
        deadline = int(time.time()) + 600

        data = router.encode_abi(
            "swapExactTokensForETH",
            args=[
                int(amount_in),
                int(out_min),
                [w3.to_checksum_address(x) for x in path],
                w3.to_checksum_address(self.client.address),
                int(deadline),
            ],
        )

        print(f"SpaceFi SWAP: USDC.e -> ETH | amount_in={amount_in} | out_min={out_min} | all={is_all_balance}")
        return await self.client.sign_and_send(to=SPACEFI_ROUTER, data=data, value=0)
