import argparse
import asyncio
import config

from src.client import AsyncEvmClient
from src.spacefi_zksync import SpaceFiZkSync


def build_parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("eth_to_usdt")
    a.add_argument("--amount", required=True, type=str)
    a.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 0.5))

    b = sub.add_parser("eth_to_wbtc")
    b.add_argument("--amount", required=True, type=str)
    b.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 0.5))

    c = sub.add_parser("usdc_e_to_eth")
    c.add_argument("--amount", required=True, type=str)
    c.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 0.5))
    c.add_argument("--all", action="store_true", help="use all USDC.e balance")

    d = sub.add_parser("usdt_to_eth")
    d.add_argument("--amount", required=True, type=str)
    d.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 0.5))
    d.add_argument("--all", action="store_true", help="use all USDT balance")

    e = sub.add_parser("usdt_to_usdc_e")
    e.add_argument("--amount", required=True, type=str)
    e.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 0.5))
    e.add_argument("--all", action="store_true", help="use all USDT balance")

    f = sub.add_parser("wbtc_to_eth")
    f.add_argument("--amount", required=True, type=str)
    f.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 0.5))
    f.add_argument("--all", action="store_true", help="use all WBTC balance")

    return p


async def run():
    args = build_parser().parse_args()

    async with AsyncEvmClient(
        rpc_url=config.ZKSYNC_RPC,
        private_key=config.PRIVATE_KEY,
        chain_id=324,
        proxy=getattr(config, "PROXY", None),
    ) as client:
        m = SpaceFiZkSync(client)

        if args.cmd == "eth_to_usdt":
            txh = await m.swap_eth_to_usdt(args.amount, args.slippage)
        elif args.cmd == "eth_to_wbtc":
            txh = await m.swap_eth_to_wbtc(args.amount, args.slippage)
        elif args.cmd == "usdc_e_to_eth":
            txh = await m.swap_usdc_e_to_eth(args.amount, args.slippage, is_all_balance=args.all)
        elif args.cmd == "usdt_to_eth":
            txh = await m.swap_usdt_to_eth(args.amount, args.slippage, is_all_balance=args.all)
        elif args.cmd == "wbtc_to_eth":
            txh = await m.swap_wbtc_to_eth(args.amount, args.slippage, is_all_balance=args.all)
        elif args.cmd == "usdt_to_usdc_e":
            txh = await m.swap_usdt_to_usdc_e(args.amount, args.slippage, is_all_balance=args.all)
        else:
            raise RuntimeError("unknown cmd")

        if not txh:
            raise RuntimeError("Tx hash is empty. Transaction was not sent.")

        if not txh.startswith("0x"):
            txh = "0x" + txh

        receipt = await client.wait_receipt(txh)
        print("tx:", txh)
        print("status:", receipt.get("status"))


if __name__ == "__main__":
    asyncio.run(run())
