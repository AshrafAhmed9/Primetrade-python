#!/usr/bin/env python3
from __future__ import annotations
"""Trading Bot v1.0 — Binance Futures Testnet"""
import argparse
import logging
import os
import sys
import time

from dotenv import load_dotenv
from rich.console import Console

from bot.client import BinanceFuturesClient
from bot.config import VERSION
from bot.exceptions import AuthenticationError, BinanceAPIError, NetworkError, ValidationError
from bot.logging_config import setup_logging
from bot.models import OrderType
from bot.orders import format_order_response, format_order_summary, place_order, place_stop_order
from bot.validators import validate_all

console = Console()
logger = logging.getLogger("trading_bot.cli")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Binance Futures Testnet Trading Bot v{VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  Verify credentials:
    python cli.py --check-auth

  Market buy:
    python cli.py --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.001

  Limit buy:
    python cli.py --symbol BTCUSDT --side BUY --order-type LIMIT --quantity 0.002 --price 45000

  Stop sell (bonus) — fires market sell when price drops to stop-price:
    python cli.py --symbol BTCUSDT --side SELL --order-type STOP --quantity 0.002 --stop-price 44000

  Dry run (no order placed):
    python cli.py --symbol BTCUSDT --side BUY --order-type LIMIT --quantity 0.002 --price 45000 --dry-run
        """,
    )
    parser.add_argument("--symbol", help="Trading pair (e.g. BTCUSDT)")
    parser.add_argument("--side", help="BUY or SELL")
    parser.add_argument("--order-type", dest="order_type", help="MARKET, LIMIT, or STOP")
    parser.add_argument("--quantity", help="Order quantity (e.g. 0.002)")
    parser.add_argument("--price", default=None, help="Limit price (required for LIMIT)")
    parser.add_argument("--stop-price", dest="stop_price", default=None, help="Stop trigger price (required for STOP)")
    parser.add_argument("--watch-timeout", dest="watch_timeout", type=int, default=60,
                        help="Seconds to watch price for STOP orders (default: 60)")
    parser.add_argument("--check-auth", action="store_true", help="Verify API credentials and exit")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview order without placing it")
    return parser.parse_args(argv)


def get_credentials() -> tuple[str, str]:
    load_dotenv()
    api_key = os.environ.get("BINANCE_API_KEY", "").strip()
    api_secret = os.environ.get("BINANCE_API_SECRET", "").strip()
    if not api_key or not api_secret:
        raise AuthenticationError(
            "BINANCE_API_KEY and BINANCE_API_SECRET must be set as environment variables.\n"
            "Copy .env.example to .env and fill in your testnet credentials."
        )
    return api_key, api_secret


def main(argv=None) -> int:
    start = time.perf_counter()
    setup_logging()

    console.print(f"[bold]Trading Bot v{VERSION}[/bold] — Binance Futures Testnet")

    try:
        args = parse_args(argv)
        api_key, api_secret = get_credentials()
        client = BinanceFuturesClient(api_key, api_secret)

        if args.check_auth:
            console.print("Checking credentials and clock sync...")
            client.check_clock_skew()
            info = client.get_account_info()
            assets = [a for a in info.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
            console.print("[green]✓ Authentication successful.[/green]")
            if assets:
                console.print("Non-zero balances:")
                for a in assets:
                    console.print(f"  {a['asset']}: {a['walletBalance']}")
            else:
                console.print("  No funded assets found (testnet account may need funding).")
            return 0

        required = ["symbol", "side", "order_type", "quantity"]
        missing = [f"--{r.replace('_', '-')}" for r in required if not getattr(args, r)]
        if missing:
            console.print(f"[red]✗ Missing required arguments: {', '.join(missing)}[/red]")
            return 1

        req = validate_all(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )

        console.print(format_order_summary(req))

        if args.dry_run:
            console.print("[yellow]⚠ Dry run — order NOT placed.[/yellow]")
            console.print("Signed params preview:", req.to_api_params())
            return 0

        answer = input("Proceed? [y/N]: ").strip().lower()
        if answer != "y":
            console.print("[yellow]⚠ Aborted.[/yellow]")
            return 0

        if req.order_type == OrderType.STOP:
            console.print(
                f"[cyan]Monitoring live price — will fire MARKET {req.side.value} "
                f"when price crosses {req.stop_price} (timeout: {args.watch_timeout}s)...[/cyan]"
            )
            response = place_stop_order(client, req, timeout=args.watch_timeout)
        else:
            with console.status("Placing order..."):
                response = place_order(client, req)

        console.print(format_order_response(response))
        console.print("[green]✓ Order placed successfully.[/green]")

    except ValidationError as e:
        for err in e.errors:
            console.print(f"[red]✗ {err}[/red]")
        logger.error("Validation failed: %s", e)
        return 1
    except BinanceAPIError as e:
        console.print(f"[red]✗ Binance API error [{e.error_code}]: {e.error_msg}[/red]")
        logger.error("Binance API error: %s", e)
        return 1
    except NetworkError as e:
        console.print("[red]✗ Could not reach Binance Testnet. Check your network.[/red]")
        logger.error("Network error: %s", e)
        return 1
    except AuthenticationError as e:
        console.print(f"[red]✗ {e}[/red]")
        logger.error("Auth error: %s", e)
        return 1
    except TimeoutError as e:
        console.print(f"[yellow]⚠ Stop order timed out: {e}[/yellow]")
        logger.warning("Stop order timeout: %s", e)
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Aborted.[/yellow]")
        return 1
    except Exception as e:
        console.print("[red]✗ Unexpected error. See logs/trading_bot.log for details.[/red]")
        logger.exception("Unexpected error: %s", e)
        return 1

    elapsed = time.perf_counter() - start
    console.print(f"[dim]Completed in {elapsed:.2f}s[/dim]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
