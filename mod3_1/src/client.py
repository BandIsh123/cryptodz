from __future__ import annotations

import os
from typing import Any
from eth_account import Account
from web3 import Web3
from web3.providers.rpc import HTTPProvider


class TxError(RuntimeError):
    pass


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
                for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"]:
            os.environ.pop(k, None)

        request_kwargs: dict[str, Any] = {"timeout": 30}

        # Если нужен прокси — используем только явный PROXY из config.py
        if self.proxy:
            request_kwargs["proxies"] = {"http": self.proxy, "https": self.proxy}

        self.w3 = Web3(HTTPProvider(self.rpc_url, request_kwargs=request_kwargs))

        # Быстрая проверка доступности RPC
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
        return w3.eth.get_transaction_count(self.address)

    async def get_tx(self, tx_hash: str) -> dict[str, Any]:
        w3 = self._require_w3()
        return dict(w3.eth.get_transaction(tx_hash))

    async def wait_receipt(self, tx_hash: str, timeout: int = 240) -> dict[str, Any]:
        w3 = self._require_w3()
        try:
            r = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        except Exception as e:
            raise TxError(f"wait_receipt failed: {e}") from e
        return dict(r)

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
        except Exception:
            tx["gasPrice"] = 1_000_000_000  # 1 gwei

        try:
            gas_est = w3.eth.estimate_gas(tx)
        except Exception as e:
            raise TxError(f"estimate_gas failed: {e}") from e
        tx["gas"] = int(gas_est * gas_multiplier)

        signed = Account.sign_transaction(tx, self.private_key)

        raw = getattr(signed, "rawTransaction", None)
        if raw is None:
            raw = getattr(signed, "raw_transaction", None)
        if raw is None:
            raise TxError("SignedTransaction has no raw tx bytes")

        try:
            tx_hash = w3.eth.send_raw_transaction(raw)
        except Exception as e:
            raise TxError(f"send_raw_transaction failed: {e}") from e

        return tx_hash.hex()
