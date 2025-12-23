from __future__ import annotations

from src.zksync_abi import SPACEFI_ROUTER_ABI
from src.zksync_tokens import TOKENS
from src.zksync_utils import now_deadline, to_wei_amount, apply_slippage, erc20, balance_erc20

SPACEFI_ROUTER = "0xbE7D1FD1f6748bbDefC4fbaCafBb11C6Fc506d1d"


class SpaceFiZkSync:
    def __init__(self, client):
        self.client = client
        self.w3 = client._require_w3()
        self.router = self.w3.eth.contract(
            address=self.w3.to_checksum_address(SPACEFI_ROUTER),
            abi=SPACEFI_ROUTER_ABI,
        )

    def _amount_out_min(self, amount_in: int, path: list[str], slippage: float) -> int:
        amounts = self.router.functions.getAmountsOut(amount_in, path).call()
        out_amt = int(amounts[-1])
        return apply_slippage(out_amt, slippage)

    async def swap_eth_to_usdt(self, eth_amount: str, slippage: float = 0.5) -> str:
        return await self._swap_eth_to_token("USDT", eth_amount, slippage)

    async def swap_eth_to_wbtc(self, eth_amount: str, slippage: float = 0.5) -> str:
        return await self._swap_eth_to_token("WBTC", eth_amount, slippage)

    async def swap_usdc_e_to_eth(self, usdc_amount: str, slippage: float = 0.5, is_all_balance: bool = False) -> str:
        usdc = TOKENS["USDC_E"]
        weth = TOKENS["WETH"]

        bal = balance_erc20(self.w3, usdc.address, self.client.address)
        amount_in = bal if is_all_balance else to_wei_amount(usdc_amount, usdc.decimals)

        if amount_in <= 0:
            raise RuntimeError("USDC_E amount_in is 0")
        if not is_all_balance and bal < amount_in:
            raise RuntimeError(f"Not enough USDC_E balance. Have={bal}, need={amount_in}")

        await self._approve_if_needed(usdc.address, amount_in, label="USDC_E")

        path = [self.w3.to_checksum_address(usdc.address), self.w3.to_checksum_address(weth.address)]
        out_min = self._amount_out_min(amount_in, path, slippage)

        data = self.router.encode_abi(
            "swapExactTokensForETH",
            args=[amount_in, out_min, path, self.w3.to_checksum_address(self.client.address), now_deadline()],
        )

        print(f"SWAP: USDC_E -> ETH, amount_in={amount_in}, out_min={out_min}")
        return await self.client.sign_and_send(to=SPACEFI_ROUTER, data=data, value=0)

    async def swap_usdt_to_eth(self, usdt_amount: str, slippage: float = 0.5, is_all_balance: bool = False) -> str:
        usdt = TOKENS["USDT"]
        weth = TOKENS["WETH"]

        bal = balance_erc20(self.w3, usdt.address, self.client.address)
        amount_in = bal if is_all_balance else to_wei_amount(usdt_amount, usdt.decimals)

        if amount_in <= 0:
            raise RuntimeError("USDT amount_in is 0")
        if not is_all_balance and bal < amount_in:
            raise RuntimeError(f"Not enough USDT balance. Have={bal}, need={amount_in}")

        await self._approve_if_needed(usdt.address, amount_in, label="USDT")

        path = [self.w3.to_checksum_address(usdt.address), self.w3.to_checksum_address(weth.address)]
        out_min = self._amount_out_min(amount_in, path, slippage)

        data = self.router.encode_abi(
            "swapExactTokensForETH",
            args=[amount_in, out_min, path, self.w3.to_checksum_address(self.client.address), now_deadline()],
        )

        print(f"SWAP: USDT -> ETH, amount_in={amount_in}, out_min={out_min}")
        return await self.client.sign_and_send(to=SPACEFI_ROUTER, data=data, value=0)
    async def swap_wbtc_to_eth(self, wbtc_amount: str, slippage: float = 0.5, is_all_balance: bool = False) -> str:
        wbtc = TOKENS["WBTC"]
        weth = TOKENS["WETH"]

        bal = balance_erc20(self.w3, wbtc.address, self.client.address)
        amount_in = bal if is_all_balance else to_wei_amount(wbtc_amount, wbtc.decimals)

        if amount_in <= 0:
            raise RuntimeError("WBTC amount_in is 0")
        if not is_all_balance and bal < amount_in:
            raise RuntimeError(f"Not enough WBTC balance. Have={bal}, need={amount_in}")

        await self._approve_if_needed(wbtc.address, amount_in, label="WBTC")

        path = [
            self.w3.to_checksum_address(wbtc.address),
            self.w3.to_checksum_address(weth.address),
        ]

        out_min = self._amount_out_min(amount_in, path, slippage)

        data = self.router.encode_abi(
            "swapExactTokensForETH",
            args=[amount_in, out_min, path, self.w3.to_checksum_address(self.client.address), now_deadline()],
        )

        print(f"SWAP: WBTC -> ETH, amount_in={amount_in}, out_min={out_min}")
        return await self.client.sign_and_send(to=SPACEFI_ROUTER, data=data, value=0)

    async def swap_usdt_to_usdc_e(self, usdt_amount: str, slippage: float = 0.5, is_all_balance: bool = False) -> str:
        usdt = TOKENS["USDT"]
        usdc = TOKENS["USDC_E"]
        weth = TOKENS["WETH"]

        bal = balance_erc20(self.w3, usdt.address, self.client.address)
        amount_in = bal if is_all_balance else to_wei_amount(usdt_amount, usdt.decimals)

        if amount_in <= 0:
            raise RuntimeError("USDT amount_in is 0")
        if not is_all_balance and bal < amount_in:
            raise RuntimeError(f"Not enough USDT balance. Have={bal}, need={amount_in}")

        await self._approve_if_needed(usdt.address, amount_in, label="USDT")

        path = [
            self.w3.to_checksum_address(usdt.address),
            self.w3.to_checksum_address(weth.address),
            self.w3.to_checksum_address(usdc.address),
        ]
        out_min = self._amount_out_min(amount_in, path, slippage)

        data = self.router.encode_abi(
            "swapExactTokensForTokens",
            args=[amount_in, out_min, path, self.w3.to_checksum_address(self.client.address), now_deadline()],
        )

        print(f"SWAP: USDT -> USDC_E, amount_in={amount_in}, out_min={out_min}")
        return await self.client.sign_and_send(to=SPACEFI_ROUTER, data=data, value=0)

    async def _swap_eth_to_token(self, to_symbol: str, eth_amount: str, slippage: float) -> str:
        weth = TOKENS["WETH"]
        token = TOKENS[to_symbol]

        amount_in = to_wei_amount(eth_amount, 18)
        path = [self.w3.to_checksum_address(weth.address), self.w3.to_checksum_address(token.address)]
        out_min = self._amount_out_min(amount_in, path, slippage)

        data = self.router.encode_abi(
            "swapExactETHForTokens",
            args=[out_min, path, self.w3.to_checksum_address(self.client.address), now_deadline()],
        )

        print(f"SWAP: ETH -> {to_symbol}, value={amount_in}, out_min={out_min}")
        return await self.client.sign_and_send(to=SPACEFI_ROUTER, data=data, value=amount_in)

    async def _approve_if_needed(self, token_addr: str, amount_in: int, label: str = "TOKEN") -> None:
        c = erc20(self.w3, token_addr)
        owner = self.w3.to_checksum_address(self.client.address)
        spender = self.w3.to_checksum_address(SPACEFI_ROUTER)

        allowance = int(c.functions.allowance(owner, spender).call())
        if allowance >= amount_in:
            return

        max_uint = (1 << 256) - 1
        approve_data = c.encode_abi("approve", args=[spender, max_uint])

        print(f"APPROVE: sending approve tx ({label})...")
        txh1 = await self.client.sign_and_send(to=token_addr, data=approve_data, value=0)
        if txh1 and not txh1.startswith("0x"):
            txh1 = "0x" + txh1
        print("approve tx:", txh1)
        await self.client.wait_receipt(txh1)
        print("APPROVE: confirmed")
