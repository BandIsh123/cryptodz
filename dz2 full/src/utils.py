from __future__ import annotations
from decimal import Decimal, ROUND_DOWN
import time

def now_ts() -> int:
    return int(time.time())

def apply_slippage(amount_out: int, slippage_pct: float) -> int:
    s = Decimal(str(slippage_pct)) / Decimal("100")
    v = (Decimal(amount_out) * (Decimal("1") - s)).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return int(v)

def to_wei_amount(amount: str, decimals: int) -> int:
    d = Decimal(str(amount))
    scale = Decimal(10) ** Decimal(decimals)
    return int((d * scale).quantize(Decimal("1"), rounding=ROUND_DOWN))

class TxError(RuntimeError):
    pass
