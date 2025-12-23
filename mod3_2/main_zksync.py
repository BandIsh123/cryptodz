import argparse
import asyncio
import config

from src.client import AsyncEvmClient
from src.koi_zksync import KoiFinance
from src.spacefi import SpaceFi
from src.maverick import Maverick, MaverickTemplate
from src.syncswap_zksync import SyncSwap, SyncSwapTemplate

MAV_TEMPLATE_USDCE_TO_MAV = "0xdae9aaf83c341094fda352b6a678a7bdce552226dc3be6a9692747eace16f6ce"
SYNC_TEMPLATE_USDCE_TO_ETH = "0xdf0c47e4bf5fd96a4a03f9777e5b91ced2bcfa43a8ad08141346d8041900782e"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    koi = sub.add_parser("koi_usdc_e_to_eth")
    koi.add_argument("--amount", required=True, type=str)
    koi.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 1.0))

    koi2 = sub.add_parser("koi_eth_to_usdc_e")
    koi2.add_argument("--amount", required=True, type=str)
    koi2.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 1.0))

    s1 = sub.add_parser("eth_to_usdt")
    s1.add_argument("--amount", required=True, type=str)
    s1.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 1.0))

    s2 = sub.add_parser("usdc_e_to_eth")
    s2.add_argument("--amount", type=str, default=None)
    s2.add_argument("--all", action="store_true")
    s2.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 1.0))

    m1 = sub.add_parser("mav_usdc_e_to_eth")
    m1.add_argument("--amount", type=str, default=None)
    m1.add_argument("--all", action="store_true")
    m1.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 1.0))

    m2 = sub.add_parser("mav_usdc_e_to_mav")
    m2.add_argument("--amount", type=str, default=None)
    m2.add_argument("--all", action="store_true")
    m2.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 1.0))

    ss = sub.add_parser("sync_usdc_e_to_eth")
    ss.add_argument("--amount", type=str, default=None)
    ss.add_argument("--all", action="store_true")
    ss.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 1.0))

    return p


async def run() -> None:
    args = build_parser().parse_args()

    async with AsyncEvmClient(
        rpc_url=getattr(config, "ZKSYNC_RPC", "https://mainnet.era.zksync.io"),
        private_key=config.PRIVATE_KEY,
        chain_id=324,
        proxy=getattr(config, "PROXY", None),
    ) as client:

        if args.cmd == "eth_to_usdt":
            m = SpaceFi(client)
            txh = await m.eth_to_usdt(args.amount, args.slippage)
            r = await client.wait_receipt(txh)
            print("tx:", txh)
            print("status:", r.get("status"))
            return

        if args.cmd == "usdc_e_to_eth":
            m = SpaceFi(client)
            txh = await m.usdc_e_to_eth(args.amount, args.slippage, is_all_balance=args.all)
            r = await client.wait_receipt(txh)
            print("tx:", txh)
            print("status:", r.get("status"))
            return

        if args.cmd == "mav_usdc_e_to_eth":
            m = Maverick(client)
            txh = await m.usdc_e_to_eth(args.amount, args.slippage, is_all_balance=args.all)
            r = await client.wait_receipt(txh)
            print("tx:", txh)
            print("status:", r.get("status"))
            return

        if args.cmd == "koi_usdc_e_to_eth":
            m = KoiFinance(client)
            txh = await m.swap_usdc_e_to_eth(args.amount, args.slippage)
            r = await client.wait_receipt(txh)
            print("tx:", txh)
            print("status:", r.get("status"))
            return

        if args.cmd == "koi_eth_to_usdc_e":
            m = KoiFinance(client)
            txh = await m.swap_eth_to_usdc_e(args.amount, args.slippage)
            r = await client.wait_receipt(txh)
            print("tx:", txh)
            print("status:", r.get("status"))
            return

        if args.cmd == "mav_usdc_e_to_mav":
            m = Maverick(
                client,
                template=MaverickTemplate(
                    tx_hash=MAV_TEMPLATE_USDCE_TO_MAV,
                    template_amount_in=1,
                ),
            )
            txh = await m.usdc_e_swap_from_template(args.amount, args.slippage, is_all_balance=args.all)
            r = await client.wait_receipt(txh)
            print("tx:", txh)
            print("status:", r.get("status"))
            return

        if args.cmd == "sync_usdc_e_to_eth":
            m = SyncSwap(client, template=SyncSwapTemplate(tx_hash=SYNC_TEMPLATE_USDCE_TO_ETH))
            txh = await m.swap_usdc_e_to_eth(args.amount, args.slippage, is_all_balance=args.all)
            r = await client.wait_receipt(txh)
            print("tx:", txh)
            print("status:", r.get("status"))
            return


if __name__ == "__main__":
    asyncio.run(run())