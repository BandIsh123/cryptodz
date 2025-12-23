import time
from decimal import Decimal, InvalidOperation
from web3 import Web3

from src.zksync_abi import ERC20_ABI_MIN


def now_deadline(seconds: int = 600) -> int:
    return int(time.time()) + seconds


def to_wei_amount(amount_str: str, decimals: int) -> int:
    try:
        d = Decimal(amount_str)
    except InvalidOperation as e:
        raise ValueError(f"Bad amount: {amount_str}") from e
    scale = Decimal(10) ** decimals
    return int(d * scale)


def apply_slippage(amount_out: int, slippage_pct: float) -> int:
    # slippage_pct = 0.5
    if slippage_pct < 0:
        raise ValueError("slippage must be >= 0")
    bps = Decimal(100) - Decimal(str(slippage_pct))
    return int(Decimal(amount_out) * bps / Decimal(100))


def erc20(w3: Web3, token_addr: str):
    return w3.eth.contract(address=w3.to_checksum_address(token_addr), abi=ERC20_ABI_MIN)


def balance_erc20(w3: Web3, token_addr: str, owner: str) -> int:
    c = erc20(w3, token_addr)
    return int(c.functions.balanceOf(w3.to_checksum_address(owner)).call())


def ensure_approve_max(client, token_addr: str, spender: str, need_amount: int) -> str | None:
    w3 = client._require_w3()
    c = erc20(w3, token_addr)

    owner = w3.to_checksum_address(client.address)
    spender = w3.to_checksum_address(spender)

    allowance = int(c.functions.allowance(owner, spender).call())
    if allowance >= need_amount:
        return None

    max_uint = (1 << 256) - 1
    data = c.encode_abi("approve", args=[spender, max_uint])

    print("APPROVE: sending approve...")
    txh = client.w3
    txh = None
    return data
