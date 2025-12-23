from web3 import AsyncWeb3

address = '0xa35ed6c81a5bb8f54efa0cdb2045ffa040fbb864'
checksum_address = AsyncWeb3.to_checksum_address(address)
print(checksum_address)  # 0xa35ed6c81a5bb8f54efa0cdb2045ffa040fbb864