from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple, Optional
from web3 import Web3

@dataclass
class TemplateSwap:
    to: str
    data: str
    value: int


def load_template_from_tx(w3: Web3, tx: dict[str, Any]) -> TemplateSwap:
    to = tx.get("to")
    data = tx.get("input") or tx.get("data")
    value = tx.get("value", 0)
    if not to or not data:
        raise ValueError("Template tx has empty 'to' or 'input'")
    return TemplateSwap(to=w3.to_checksum_address(to), data=data, value=int(value))


def replace_uint256_in_calldata(data_hex: str, old_value: int, new_value: int) -> str:

    h = data_hex[2:] if data_hex.startswith("0x") else data_hex
    old_hex = f"{old_value:064x}"
    new_hex = f"{new_value:064x}"
    idx = h.find(old_hex)
    if idx < 0:
        raise ValueError("old_value not found in calldata")
    h2 = h[:idx] + new_hex + h[idx+64:]
    return "0x" + h2
