import argparse
import asyncio
import config

from src.client import AsyncEvmClient
from src.l2pass import L2PassMinter
from src.quickswap import QuickSwap


def build_parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    l2 = sub.add_parser("l2pass")
    l2.add_argument("--qty", type=int, default=1)
    l2.add_argument("--value", type=str, default="1")
    l2.add_argument("--template-tx", type=str, default=None)

    sw = sub.add_parser("swap")
    sw.add_argument("--from", dest="from_token", required=True)
    sw.add_argument("--to", dest="to_token", required=True)
    sw.add_argument("--amount", required=True, type=str)
    sw.add_argument("--slippage", type=float, default=getattr(config, "SLIPPAGE", 0.5))

    return p


async def run():
    args = build_parser().parse_args()

    print("CMD:", args.cmd)
    print("ARGS:", args)

    client = AsyncEvmClient(
        rpc_url=config.POLYGON_RPC,
        private_key=config.PRIVATE_KEY,
        chain_id=137,
        proxy=getattr(config, "PROXY", None),
    )

    async with client:
        if client.w3 is None:
            raise RuntimeError("Web3 not initialized (client.w3 is None)")

        if args.cmd == "l2pass":
            minter = L2PassMinter(client)

            print("L2PASS: mint start...")
            if args.template_tx:
                txh = await minter.mint_from_template_tx(args.template_tx)
            else:
                txh = await minter.mint(quantity=args.qty, value_pol=args.value)

            if not txh:
                raise RuntimeError("Tx hash is empty. Transaction was not sent.")

            # нормализуем вывод
            if not txh.startswith("0x"):
                txh = "0x" + txh

            receipt = await client.wait_receipt(txh)
            print("tx:", txh)
            print("status:", receipt.get("status"))
            return

        if args.cmd == "swap":
            qs = QuickSwap(client)

            print(f"SWAP: {args.from_token} -> {args.to_token}, amount={args.amount}, slippage={args.slippage}%")
            txh = await qs.swap(args.from_token, args.to_token, args.amount, args.slippage)

            if not txh:
                raise RuntimeError("Tx hash is empty. Transaction was not sent.")

            if not txh.startswith("0x"):
                txh = "0x" + txh

            receipt = await client.wait_receipt(txh)
            print("tx:", txh)
            print("status:", receipt.get("status"))
            return


if __name__ == "__main__":
    asyncio.run(run())
