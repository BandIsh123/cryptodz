from __future__ import annotations

from decimal import Decimal
from web3 import Web3


def to_wei(amount: str, decimals: int) -> int:
    x = Decimal(str(amount))
    scale = Decimal(10) ** decimals
    return int(x * scale)


def from_wei(value: int, decimals: int) -> Decimal:
    return Decimal(value) / (Decimal(10) ** decimals)


def encode_erc20_approve(w3: Web3, token: str, spender: str, amount: int) -> str:
    abi = [
        {
            "name": "approve",
            "type": "function",
            "stateMutability": "nonpayable",
            "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "outputs": [{"name": "", "type": "bool"}],
        }
    ]
    c = w3.eth.contract(address=w3.to_checksum_address(token), abi=abi)
    return c.encode_abi("approve", args=[w3.to_checksum_address(spender), int(amount)])


def erc20_balance_of(w3: Web3, token: str, owner: str) -> int:
    abi = [
        {
            "name": "balanceOf",
            "type": "function",
            "stateMutability": "view",
            "inputs": [{"name": "owner", "type": "address"}],
            "outputs": [{"name": "", "type": "uint256"}],
        }
    ]
    c = w3.eth.contract(address=w3.to_checksum_address(token), abi=abi)
    return int(c.functions.balanceOf(w3.to_checksum_address(owner)).call())


def erc20_allowance(w3: Web3, token: str, owner: str, spender: str) -> int:
    abi = [
        {
            "name": "allowance",
            "type": "function",
            "stateMutability": "view",
            "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
            "outputs": [{"name": "", "type": "uint256"}],
        }
    ]
    c = w3.eth.contract(address=w3.to_checksum_address(token), abi=abi)
    return int(
        c.functions.allowance(w3.to_checksum_address(owner), w3.to_checksum_address(spender)).call()
    )
