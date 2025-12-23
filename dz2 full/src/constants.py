from dataclasses import dataclass

@dataclass(frozen=True)
class Token:
    name: str
    address: str | None
    decimals: int

USDC = Token("USDC", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", 6)
WPOL = Token("WPOL", "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270", 18)
POL = Token("POL", None, 18)

QUICKSWAP_V2_ROUTER = "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"

TOKENS_BY_NAME = {"POL": POL, "USDC": USDC, "WPOL": WPOL}
