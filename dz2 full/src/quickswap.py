from __future__ import annotations

from typing import List

from src.abi import ERC20_ABI, UNISWAP_V2_ROUTER_ABI
from src.constants import QUICKSWAP_V2_ROUTER, TOKENS_BY_NAME, WPOL
from src.utils import apply_slippage, now_ts, to_wei_amount


class QuickSwap:
    def __init__(self, client):
        self.client = client

    def _router(self):
        w3 = self.client._require_w3()
        return w3.eth.contract(
            address=w3.to_checksum_address(QUICKSWAP_V2_ROUTER),
            abi=UNISWAP_V2_ROUTER_ABI,
        )

    def _erc20(self, token_addr: str):
        w3 = self.client._require_w3()
        return w3.eth.contract(
            address=w3.to_checksum_address(token_addr),
            abi=ERC20_ABI,
        )

    async def _ensure_approval(self, token_addr: str, spender: str, amount: int) -> str | None:
        w3 = self.client._require_w3()
        token = self._erc20(token_addr)

        allowance = token.functions.allowance(
            self.client.address,
            w3.to_checksum_address(spender),
        ).call()

        if allowance >= amount:
            return None

        max_uint = (1 << 256) - 1
        data = token.encode_abi("approve", args=[w3.to_checksum_address(spender), max_uint])

        print("APPROVE: sending approve tx...")
        approve_txh = await self.client.sign_and_send(to=token_addr, data=data, value=0)

        if approve_txh and not approve_txh.startswith("0x"):
            approve_txh = "0x" + approve_txh

        print("APPROVE tx:", approve_txh)
        await self.client.wait_receipt(approve_txh)
        print("APPROVE: confirmed")
        return approve_txh

    def _get_amount_out_min(self, amount_in: int, path: List[str], slippage_pct: float) -> int:
        router = self._router()
        amounts = router.functions.getAmountsOut(amount_in, path).call()
        amount_out = int(amounts[-1])
        return apply_slippage(amount_out, slippage_pct)

    async def swap(self, from_token_name: str, to_token_name: str, amount: str, slippage: float) -> str:
        w3 = self.client._require_w3()

        from_t = TOKENS_BY_NAME[from_token_name.upper()]
        to_t = TOKENS_BY_NAME[to_token_name.upper()]

        router = self._router()
        deadline = now_ts() + 600

        def c(addr: str) -> str:
            return w3.to_checksum_address(addr)

        if from_t.address is None and to_t.address is None:
            raise ValueError("POL -> POL swap is not meaningful")

        # POL -> token
        if from_t.address is None:
            amount_in = to_wei_amount(amount, 18)
            path = [c(WPOL.address), c(to_t.address)]
            out_min = self._get_amount_out_min(amount_in, path, slippage)

            data = router.encode_abi(
                "swapExactETHForTokens",
                args=[out_min, path, self.client.address, deadline],
            )

            print("SWAP: sending POL->TOKEN tx...")
            txh = await self.client.sign_and_send(to=QUICKSWAP_V2_ROUTER, data=data, value=amount_in)
            return txh

        # token -> POL
        if to_t.address is None:
            amount_in = to_wei_amount(amount, from_t.decimals)
            path = [c(from_t.address), c(WPOL.address)]

            await self._ensure_approval(from_t.address, QUICKSWAP_V2_ROUTER, amount_in)

            out_min = self._get_amount_out_min(amount_in, path, slippage)
            data = router.encode_abi(
                "swapExactTokensForETH",
                args=[amount_in, out_min, path, self.client.address, deadline],
            )

            print("SWAP: sending TOKEN->POL tx...")
            txh = await self.client.sign_and_send(to=QUICKSWAP_V2_ROUTER, data=data, value=0)
            return txh

        # token -> token
        amount_in = to_wei_amount(amount, from_t.decimals)
        await self._ensure_approval(from_t.address, QUICKSWAP_V2_ROUTER, amount_in)

        if from_t.address.lower() == WPOL.address.lower() or to_t.address.lower() == WPOL.address.lower():
            path = [c(from_t.address), c(to_t.address)]
        else:
            path = [c(from_t.address), c(WPOL.address), c(to_t.address)]

        out_min = self._get_amount_out_min(amount_in, path, slippage)
        data = router.encode_abi(
            "swapExactTokensForTokens",
            args=[amount_in, out_min, path, self.client.address, deadline],
        )

        print("SWAP: sending TOKEN->TOKEN tx...")
        txh = await self.client.sign_and_send(to=QUICKSWAP_V2_ROUTER, data=data, value=0)
        return txh
