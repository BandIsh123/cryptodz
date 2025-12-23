import asyncio

from web3 import AsyncWeb3


async def main():
    rpc = 'wss://ethereum-rpc.publicnode.com'
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc))

    address = '0xa35ed6c81a5bb8f54efa0cdb2045ffa040fbb864'
    checksum_address = AsyncWeb3.to_checksum_address(address)
    balance = await w3.eth.get_balance(checksum_address)
    print(f'balance: {balance} Wei')
    print(f'balance: {balance / 10 ** 18} ETH')
    print(AsyncWeb3.from_wei(balance, 'ether'))  # 1
    print(AsyncWeb3.from_wei(balance, 'tether'))  # 0.000000000001

if __name__ == '__main__':
    asyncio.run(main())