from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import requests
from eth_account import Account
from web3 import Web3
from web3.providers.rpc import HTTPProvider


class TxError(RuntimeError):
    pass


@dataclass
class PriceFeed:
    base: str
    quote: str = "USDT"


class AsyncEvmClient:

    def __init__(self, rpc_url: str, private_key: str, chain_id: int, proxy: str | None = None):
        self.rpc_url = rpc_url
        self.private_key = private_key
        self.chain_id = chain_id
        self.proxy = proxy

        self.account = Account.from_key(private_key)
        self.address = self.account.address

        self.w3: Web3 | None = None

    async def __aenter__(self) -> "AsyncEvmClient":
        request_kwargs: dict[str, Any] = {"timeout": 60}
        if self.proxy:

            request_kwargs["proxies"] = {"http": self.proxy, "https": self.proxy}

        self.w3 = Web3(HTTPProvider(self.rpc_url, request_kwargs=request_kwargs))
        if not self.w3.is_connected():
            raise RuntimeError(f"RPC not connected: {self.rpc_url}")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.w3 = None

    def _require_w3(self) -> Web3:
        if self.w3 is None:
            raise RuntimeError("Client not initialized")
        return self.w3

    async def get_nonce(self) -> int:
        w3 = self._require_w3()
        return w3.eth.get_transaction_count(self.address, "pending")

    async def sign_and_send(self, to: str, data: str = "0x", value: int = 0, gas_multiplier: float = 1.15) -> str:
        w3 = self._require_w3()
        nonce = await self.get_nonce()

        tx: dict[str, Any] = {
            "chainId": self.chain_id,
            "from": self.address,
            "to": w3.to_checksum_address(to),
            "nonce": nonce,
            "data": data,
            "value": int(value),
        }


        try:
            tx["gasPrice"] = int(w3.eth.gas_price)
        except Exception as e:
            raise TxError(f"gas_price failed: {e}") from e

        try:
            gas_est = w3.eth.estimate_gas(tx)
        except Exception as e:
            raise TxError(f"estimate_gas failed: {e}") from e

        tx["gas"] = int(gas_est * gas_multiplier)

        signed = Account.sign_transaction(tx, self.private_key)

        # web3.py v6+: raw_transaction (а не rawTransaction)
        raw = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction", None)
        if raw is None:
            raise TxError("SignedTransaction has no raw tx field (rawTransaction/raw_transaction)")

        try:
            tx_hash = w3.eth.send_raw_transaction(raw)
        except Exception as e:
            raise TxError(f"send_raw_transaction failed: {e}") from e

        return tx_hash.hex()

    async def wait_receipt(self, tx_hash: str, timeout: int = 240) -> dict[str, Any]:
        w3 = self._require_w3()
        try:
            r = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        except Exception as e:
            raise TxError(f"wait_receipt failed: {e}") from e
        return dict(r)

    async def get_tx(self, tx_hash: str) -> dict:

        w3 = self._require_w3()
        return dict(w3.eth.get_transaction(tx_hash))


    async def get_token_price_binance(self, symbol: str) -> Optional[float]:

        s = symbol.upper()
        if s in ("WETH", "ETH"):
            s = "ETH"
        if s == "WBTC":
            s = "BTC"
        if s in ("USDT", "USDC", "USDC.E"):
            return 1.0

        url = f"https://api.binance.com/api/v3/depth?limit=1&symbol={s}USDT"
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None

        for _ in range(5):
            try:
                r = requests.get(url, timeout=15, proxies=proxies)
                j = r.json()
                asks = j.get("asks")
                if asks:
                    return float(asks[0][0])
                return None
            except Exception:
                continue
        return None
