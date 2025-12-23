import asyncio
from web3 import AsyncWeb3

RPC = "https://eth.llamarpc.com"

# USDT (ERC20)
USDT = AsyncWeb3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")
USDT_ABI = [{
    "constant": True,
    "inputs": [{"name": "_owner", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "balance", "type": "uint256"}],
    "type": "function"
}]


async def get_random_addresses_from_blocks(w3, blocks=50, needed=10):
    addresses = set()
    latest = await w3.eth.block_number

    for i in range(blocks):
        block = await w3.eth.get_block(latest - i, full_transactions=True)

        for tx in block.transactions:
            if tx['from']:
                addresses.add(tx['from'])
            if tx['to']:
                addresses.add(tx['to'])

            if len(addresses) >= needed:
                return list(addresses)

    return list(addresses)


async def get_usdt_balance(contract, address):
    try:
        bal = await contract.functions.balanceOf(address).call()
        return bal / 1e6  # USDT = 6 decimals
    except:
        return 0


async def main():
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC))
    contract = w3.eth.contract(address=USDT, abi=USDT_ABI)

    print("Собираю случайные адреса из блокчейна...\n")

    addresses = await get_random_addresses_from_blocks(w3)
    print("Найденные адреса:", addresses, "\n")

    results = []
    for a in addresses:
        bal = await get_usdt_balance(contract, a)
        results.append((a, bal))
        print(f"{a} → {bal} USDT")

    print("\n=== ОТСОРТИРОВАНО ===\n")
    results.sort(key=lambda x: x[1], reverse=True)

    for addr, bal in results:
        print(f"{addr}: {bal} USDT")


if __name__ == "__main__":
    asyncio.run(main())
