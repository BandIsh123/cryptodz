from __future__ import annotations
from .client import AsyncEvmClient
from .utils import to_wei_amount

class L2PassMinter:
    CONTRACT = "0x042002711e4d7A7Fc486742a85dBf096beeb0420"
    ABI = [{
        "name":"mint",
        "type":"function",
        "stateMutability":"payable",
        "inputs":[{"name":"n","type":"uint256"}],
        "outputs":[]
    }]

    def __init__(self, client: AsyncEvmClient):
        self.client = client

    def _contract(self):
        w3 = self.client._require_w3()
        return w3.eth.contract(address=w3.to_checksum_address(self.CONTRACT), abi=self.ABI)

    async def mint(self, quantity: int=1, value_pol: str="1") -> str:
        c = self._contract()
        data = c.encode_abi("mint", args=[int(quantity)])
        value = to_wei_amount(value_pol, 18)
        return await self.client.sign_and_send(to=self.CONTRACT, data=data, value=value)

    async def mint_from_template_tx(self, template_tx_hash: str) -> str:
        tx = await self.client.get_tx(template_tx_hash)
        to = tx.get("to")
        data = tx.get("input") or tx.get("data") or "0x"
        value = int(tx.get("value", 0))
        return await self.client.sign_and_send(to=to, data=data, value=value)
