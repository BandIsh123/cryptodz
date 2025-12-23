from __future__ import annotations

from web3 import Web3

ZERO = "0x0000000000000000000000000000000000000000"

# zkSync Era tokens
WETH = "0x5aea5775959fbc2557cc8789bc1bf90a239d9a91"
USDC_E = "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4"
USDT = "0x493257fd37edb34451f62edf8d2a0c418852ba4c"
MAV = "0x787c09494Ec8Bcb24DcAf8659E7d5D69979eE508"

ERC20_ABI = [
    {"name": "balanceOf", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "owner", "type": "address"}],
     "outputs": [{"name": "balance", "type": "uint256"}]},
    {"name": "allowance", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
     "outputs": [{"name": "amount", "type": "uint256"}]},
    {"name": "approve", "type": "function", "stateMutability": "nonpayable",
     "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "outputs": [{"name": "ok", "type": "bool"}]},
    {"name": "decimals", "type": "function", "stateMutability": "view",
     "inputs": [],
     "outputs": [{"name": "", "type": "uint8"}]},
]

WETH_ABI = ERC20_ABI + [
    {"name": "withdraw", "type": "function", "stateMutability": "nonpayable",
     "inputs": [{"name": "wad", "type": "uint256"}],
     "outputs": []},
]


def _erc20(w3: Web3, token: str):
    return w3.eth.contract(address=w3.to_checksum_address(token), abi=ERC20_ABI)


def _weth(w3: Web3):
    return w3.eth.contract(address=w3.to_checksum_address(WETH), abi=WETH_ABI)


def balance_of(w3: Web3, token: str, owner: str) -> int:
    return int(_erc20(w3, token).functions.balanceOf(w3.to_checksum_address(owner)).call())


def allowance(w3: Web3, token: str, owner: str, spender: str) -> int:
    return int(_erc20(w3, token).functions.allowance(
        w3.to_checksum_address(owner),
        w3.to_checksum_address(spender),
    ).call())


def encode_approve(w3: Web3, token: str, spender: str, amount: int) -> str:
    return _erc20(w3, token).encode_abi("approve", args=[w3.to_checksum_address(spender), int(amount)])


def encode_withdraw_weth(w3: Web3, amount_wei: int) -> str:
    return _weth(w3).encode_abi("withdraw", args=[int(amount_wei)])
