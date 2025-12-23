import asyncio

from web3 import AsyncWeb3


async def main():
    # баланс в Wei
    balance = 1_000_000_000_000_000_000
    print(balance)  # 1000000000000000000

    print(AsyncWeb3.from_wei(balance, 'kwei'))  # 1000000000000000
    print(AsyncWeb3.from_wei(balance, 'babbage'))  # 1000000000000000
    print(AsyncWeb3.from_wei(balance, 'femtoether'))  # 1000000000000000

    print(AsyncWeb3.from_wei(balance, 'mwei'))  # 1000000000000
    print(AsyncWeb3.from_wei(balance, 'lovelace'))  # 1000000000000
    print(AsyncWeb3.from_wei(balance, 'picoether'))  # 1000000000000

    print(AsyncWeb3.from_wei(balance, 'gwei'))  # 1000000000
    print(AsyncWeb3.from_wei(balance, 'shannon'))  # 1000000000
    print(AsyncWeb3.from_wei(balance, 'nanoether'))  # 1000000000
    print(AsyncWeb3.from_wei(balance, 'nano'))  # 1000000000

    print(AsyncWeb3.from_wei(balance, 'szabo'))  # 1000000
    print(AsyncWeb3.from_wei(balance, 'microether'))  # 1000000
    print(AsyncWeb3.from_wei(balance, 'micro'))  # 1000000

    print(AsyncWeb3.from_wei(balance, 'finney'))  # 1000
    print(AsyncWeb3.from_wei(balance, 'milliether'))  # 1000
    print(AsyncWeb3.from_wei(balance, 'milli'))  # 1000

    print(AsyncWeb3.from_wei(balance, 'ether'))  # 1

    print(AsyncWeb3.from_wei(balance, 'kether'))  # 0.001
    print(AsyncWeb3.from_wei(balance, 'grand'))  # 0.001

    print(AsyncWeb3.from_wei(balance, 'mether'))  # 0.000001

    print(AsyncWeb3.from_wei(balance, 'gether'))  # 0.000000001

    print(AsyncWeb3.from_wei(balance, 'tether'))  # 0.000000000001


if __name__ == '__main__':
    asyncio.run(main())