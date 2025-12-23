import asyncio

from web3 import AsyncWeb3


async def main():
    rpc = 'wss://ethereum-rpc.publicnode.com'
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc))
    print(await w3.is_connected())  # True


if __name__ == '__main__':
    asyncio.run(main())