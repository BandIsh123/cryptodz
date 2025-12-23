from dataclasses import dataclass

@dataclass(frozen=True)
class Token:
    symbol: str
    address: str | None
    decimals: int

# Native ETH
ETH = Token("ETH", None, 18)

# Wrapped ETH
WETH = Token("WETH", "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91", 18)

USDT = Token("USDT", "0x493257fd37edb34451f62edf8d2a0c418852ba4c", 6)
USDC_E = Token("USDC_E", "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4", 6)
WBTC = Token("WBTC", "0xBBeB516fb02a01611cBBE0453Fe3c580D7281011", 8)

TOKENS = {
    "ETH": ETH,
    "WETH": WETH,
    "USDT": USDT,
    "USDC_E": USDC_E,
    "WBTC": WBTC,
}
