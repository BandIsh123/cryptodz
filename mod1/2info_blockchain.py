import asyncio

from web3 import AsyncWeb3


async def main():
    rpc = 'wss://ethereum-rpc.publicnode.com'
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc))

    # Получение gas_price
    gas_price = await w3.eth.gas_price
    print(f"gas price: {gas_price} Wei")
    print(f"gas price: {gas_price / 10 ** 9} GWei")
    print(f"gas price: {gas_price / 10 ** 18} ETH")

    # Получение max_priority_fee (для EIP-1559 транзакций. Работает не во всех сетях)
    max_priority_fee = await w3.eth.max_priority_fee
    print(f"max priority fee: {max_priority_fee}")

    # Получение id сети
    chain_id = await w3.eth.chain_id
    print(f"number of current chain is {chain_id}")

    # Получение номера текущего блока
    block_number = await w3.eth.block_number
    print(f"current block number: {block_number}")


if __name__ == '__main__':
    asyncio.run(main())