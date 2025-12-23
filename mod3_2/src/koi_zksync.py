from __future__ import annotations

from decimal import Decimal
from web3 import Web3

from src.client import AsyncEvmClient
from src.tokens import USDC_E, WETH, balance_of, allowance, encode_approve

# USDC.e / WETH pair (KOI)
KOI_PAIR = Web3.to_checksum_address("0xDFAaB828f5F515E104BaaBa4d8D554DA9096f0e4")

USDC_E = Web3.to_checksum_address(USDC_E)
WETH = Web3.to_checksum_address(WETH)

PAIR_ABI = [
    {
        "name": "swap",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "amount0Out", "type": "uint256"},
            {"name": "amount1Out", "type": "uint256"},
            {"name": "to", "type": "address"},
            {"name": "data", "type": "bytes"},
        ],
        "outputs": [],
    },
    {
        "name": "getReserves",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [
            {"name": "reserve0", "type": "uint112"},
            {"name": "reserve1", "type": "uint112"},
            {"name": "blockTimestampLast", "type": "uint32"},
        ],
    },
]

ERC20_TRANSFER_ABI = [
    {
        "name": "transfer",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"type": "bool"}],
    }
]

WETH_ABI = [
    {
        "name": "deposit",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [],
        "outputs": [],
    },
    {
        "name": "withdraw",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "wad", "type": "uint256"}],
        "outputs": [],
    },
    {
        "name": "transfer",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
        ],
        "outputs": [{"type": "bool"}],
    },
]


def to_wei(amount: str, decimals: int) -> int:
    return int(Decimal(str(amount)) * (Decimal(10) ** decimals))


def get_amount_out(amount_in: int, reserve_in: int, reserve_out: int) -> int:
    # UniswapV2 0.3% fee
    amount_in_with_fee = amount_in * 997
    numerator = amount_in_with_fee * reserve_out
    denominator = reserve_in * 1000 + amount_in_with_fee
    return numerator // denominator


class KoiFinance:


    def __init__(self, client: AsyncEvmClient):
        self.client = client

    def _w3(self) -> Web3:
        return self.client._require_w3()

    async def swap_eth_to_usdc_e(self, eth_amount: str, slippage: float = 1.0) -> str:

        w3 = self._w3()
        pair = w3.eth.contract(address=KOI_PAIR, abi=PAIR_ABI)
        weth = w3.eth.contract(address=WETH, abi=WETH_ABI)

        amount_in = to_wei(eth_amount, 18)
        if amount_in <= 0:
            raise ValueError("amount_in == 0")

        # wrap ETH -> WETH
        tx = await self.client.sign_and_send(
            to=WETH,
            data=weth.encode_abi("deposit", args=[]),
            value=amount_in,
        )
        await self.client.wait_receipt(tx)

        # reserves: token0=USDC.e, token1=WETH
        r0, r1, _ = pair.functions.getReserves().call()
        expected_out = get_amount_out(amount_in, int(r1), int(r0))
        out_min = int(expected_out * (1 - slippage / 100))

        # approve WETH
        if allowance(w3, WETH, self.client.address, KOI_PAIR) < amount_in:
            approve = encode_approve(w3, WETH, KOI_PAIR, 2**256 - 1)
            tx = await self.client.sign_and_send(to=WETH, data=approve, value=0)
            await self.client.wait_receipt(tx)

        # transfer WETH -> pair (CRITICAL)
        tx = await self.client.sign_and_send(
            to=WETH,
            data=weth.encode_abi("transfer", args=[KOI_PAIR, int(amount_in)]),
            value=0,
        )
        await self.client.wait_receipt(tx)

        # swap: USDC.e
        swap_data = pair.encode_abi(
            "swap",
            args=[int(out_min), 0, self.client.address, b""],
        )

        print(f"KOI SWAP ETH->USDC.e | in={amount_in} out_min={out_min}")
        return await self.client.sign_and_send(to=KOI_PAIR, data=swap_data, value=0)

    async def swap_usdc_e_to_eth(
        self,
        usdc_amount: str | None,
        slippage: float = 1.0,
        is_all_balance: bool = False,
    ) -> str:

        w3 = self._w3()
        pair = w3.eth.contract(address=KOI_PAIR, abi=PAIR_ABI)
        weth = w3.eth.contract(address=WETH, abi=WETH_ABI)
        usdc = w3.eth.contract(address=USDC_E, abi=ERC20_TRANSFER_ABI)

        # amount_in: support "--amount 0" as "all"
        if is_all_balance or usdc_amount in (None, "0", 0):
            amount_in = balance_of(w3, USDC_E, self.client.address)
        else:
            amount_in = to_wei(usdc_amount, 6)

        if amount_in <= 0:
            raise ValueError("amount_in == 0")


        r0, r1, _ = pair.functions.getReserves().call()
        expected_out = get_amount_out(int(amount_in), int(r0), int(r1))
        out_min = int(expected_out * (1 - slippage / 100))

        # approve USDC.e
        if allowance(w3, USDC_E, self.client.address, KOI_PAIR) < amount_in:
            approve = encode_approve(w3, USDC_E, KOI_PAIR, 2**256 - 1)
            tx = await self.client.sign_and_send(to=USDC_E, data=approve, value=0)
            await self.client.wait_receipt(tx)

        # transfer USDC.e -> pair
        tx = await self.client.sign_and_send(
            to=USDC_E,
            data=usdc.encode_abi("transfer", args=[KOI_PAIR, int(amount_in)]),
            value=0,
        )
        await self.client.wait_receipt(tx)

        # swap: WETH
        swap_data = pair.encode_abi(
            "swap",
            args=[0, int(out_min), self.client.address, b""],
        )

        print(f"KOI SWAP USDC.e->WETH | in={amount_in} out_min={out_min}")
        tx_swap = await self.client.sign_and_send(to=KOI_PAIR, data=swap_data, value=0)
        await self.client.wait_receipt(tx_swap)

        # unwrap all WETH received
        weth_bal = balance_of(w3, WETH, self.client.address)
        if weth_bal > 0:
            unwrap_data = weth.encode_abi("withdraw", args=[int(weth_bal)])
            print(f"Unwrap WETH->ETH | weth_bal={weth_bal}")
            return await self.client.sign_and_send(to=WETH, data=unwrap_data, value=0)


        return tx_swap
