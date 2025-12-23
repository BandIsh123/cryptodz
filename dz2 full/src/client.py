from __future__ import annotations

from typing import Any
from eth_account import Account
from web3 import Web3
from web3.providers.rpc import HTTPProvider


class TxError(RuntimeError):
    pass


class AsyncEvmClient:
    """
    Упрощённый клиент: использует только sync Web3 (HTTPProvider),
    но API оставляем async, чтобы ваш код (await/asyncio) не менять.

    Это самый стабильный вариант под Windows + PyCharm.
    """

    def __init__(self, rpc_url: str, private_key: str, chain_id: int, proxy: str | None = None):
        self.rpc_url = rpc_url
        self.private_key = private_key
        self.chain_id = chain_id
        self.proxy = proxy

        self.account = Account.from_key(private_key)
        self.address = self.account.address

        self.w3: Web3 | None = None

    async def __aenter__(self) -> "AsyncEvmClient":
        request_kwargs: dict[str, Any] = {}
        if self.proxy:
            # requests ожидает proxies, не proxy
            request_kwargs["proxies"] = {"http": self.proxy, "https": self.proxy}

        self.w3 = Web3(HTTPProvider(self.rpc_url, request_kwargs=request_kwargs))
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

    async def sign_and_send(self, to: str, data: str = "0x", value: int = 0, gas_multiplier: float = 1.15) -> str:
        w3 = self._require_w3()

        nonce = await self.get_nonce()
        tx: dict[str, Any] = {
            "chainId": self.chain_id,
            "from": self.address,
            "to": w3.to_checksum_address(to),
            "nonce": nonce,
            "data": data,
            "value": value,
        }

        # EIP-1559 если доступно
        try:
            block = w3.eth.get_block("latest")
            base_fee = block["baseFeePerGas"]
            prio = w3.eth.max_priority_fee
            tx["maxPriorityFeePerGas"] = int(prio)
            tx["maxFeePerGas"] = int(base_fee * 2 + prio)
            tx["type"] = 2
        except Exception:
            tx["gasPrice"] = w3.eth.gas_price

        try:
            gas_est = w3.eth.estimate_gas(tx)
        except Exception as e:
            raise TxError(f"estimate_gas failed: {e}") from e
        tx["gas"] = int(gas_est * gas_multiplier)

        signed = Account.sign_transaction(tx, self.private_key)

        raw = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction", None)
        if raw is None:
            raise TxError("Signing failed: no raw transaction field on SignedTransaction")

        try:
            tx_hash_bytes = w3.eth.send_raw_transaction(raw)
        except Exception as e:
            raise TxError(f"send_raw_transaction failed: {e}") from e

        # web3 может вернуть HexBytes или bytes
        txh = tx_hash_bytes.hex() if hasattr(tx_hash_bytes, "hex") else str(tx_hash_bytes)

        if not txh or txh == "None":
            raise TxError("send_raw_transaction returned empty tx hash")

        return txh

    async def wait_receipt(self, tx_hash: str, timeout: int = 180) -> dict[str, Any]:
        w3 = self._require_w3()
        try:
            r = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        except Exception as e:
            raise TxError(f"wait_receipt failed: {e}") from e
        return dict(r)

    async def get_tx(self, tx_hash: str) -> dict[str, Any]:
        w3 = self._require_w3()
        return dict(w3.eth.get_transaction(tx_hash))
