# xevvor.py
# pip install requests yfinance rich
# pip install requests yfinance

import json
import os
import sys
import time
from datetime import datetime

import requests
import yfinance as yf
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

CONFIG_FILE = "xevvor_config.json"
CHECK_INTERVAL_SECONDS = 600

console = Console()

CRYPTO_ALIASES = {
    "btc": "bitcoin", "bitcoin": "bitcoin", "xbt": "bitcoin", "bit": "bitcoin", "bitcoi": "bitcoin",
    "eth": "ethereum", "ether": "ethereum", "ethereum": "ethereum", "ethereu": "ethereum", "ethe": "ethereum",
    "sol": "solana", "solana": "solana",
    "doge": "dogecoin", "dogecoin": "dogecoin",
    "ltc": "litecoin", "litecoin": "litecoin",
    "xrp": "ripple", "ripple": "ripple",
    "ada": "cardano", "cardano": "cardano",
    "dot": "polkadot", "polkadot": "polkadot",
    "link": "chainlink", "chainlink": "chainlink",
    "avax": "avalanche-2", "avalanche": "avalanche-2",
    "matic": "matic-network", "polygon": "matic-network", "pol": "matic-network",
    "bnb": "binancecoin", "binance": "binancecoin", "binancecoin": "binancecoin",
    "usdt": "tether", "tether": "tether",
    "usdc": "usd-coin", "usd coin": "usd-coin",
    "trx": "tron", "tron": "tron",
    "shib": "shiba-inu", "shiba": "shiba-inu", "shiba inu": "shiba-inu",
    "xmr": "monero", "monero": "monero",
    "xlm": "stellar", "stellar": "stellar",
    "atom": "cosmos", "cosmos": "cosmos",
    "near": "near", "near protocol": "near",
    "arb": "arbitrum", "arbitrum": "arbitrum",
    "op": "optimism", "optimism": "optimism",
    "pepe": "pepe",
}


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def intro():
    clear()
    logo = r"""
██╗  ██╗███████╗██╗   ██╗██╗   ██╗ ██████╗ ██████╗ 
╚██╗██╔╝██╔════╝██║   ██║██║   ██║██╔═══██╗██╔══██╗
 ╚███╔╝ █████╗  ██║   ██║██║   ██║██║   ██║██████╔╝
 ██╔██╗ ██╔══╝  ╚██╗ ██╔╝╚██╗ ██╔╝██║   ██║██╔══██╗
██╔╝ ██╗███████╗ ╚████╔╝  ╚████╔╝ ╚██████╔╝██║  ██║
╚═╝  ╚═╝╚══════╝  ╚═══╝    ╚═══╝   ╚═════╝ ╚═╝  ╚═╝
"""
    console.print(Text(logo, style="bold bright_green"))
    console.print(
        Panel.fit(
            "[bold bright_green]XEVVOR MARKET WATCH[/bold bright_green]\n"
            "[bright_black]// asset surveillance daemon initialized[/bright_black]\n"
            "[cyan]// discord transmission module armed[/cyan]",
            border_style="bright_green",
        )
    )


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def ask_webhook(config):
    saved = config.get("discord_webhook")

    if saved:
        console.print(f"[green]Saved webhook found:[/green] {saved[:55]}...")
        if Confirm.ask("Use saved webhook?", default=True):
            return saved

    while True:
        webhook = Prompt.ask("[bright_green]Paste Discord webhook URL[/bright_green]").strip()

        if not webhook:
            console.print("[red]Webhook cannot be empty.[/red]")
            continue

        if not webhook.startswith("https://discord.com/api/webhooks/"):
            console.print("[red]That does not look like a Discord webhook URL.[/red]")
            continue

        config["discord_webhook"] = webhook
        save_config(config)
        return webhook


def ask_everyone_ping(config):
    if "ping_everyone" in config:
        console.print(f"[cyan]Saved @everyone setting:[/cyan] {config['ping_everyone']}")
        if Confirm.ask("Use saved @everyone setting?", default=True):
            return bool(config["ping_everyone"])

    enabled = Confirm.ask("[yellow]Ping @everyone on every 10-minute update?[/yellow]", default=False)
    config["ping_everyone"] = enabled
    save_config(config)
    return enabled


def resolve_crypto_id(text):
    cleaned = " ".join(text.strip().lower().split())
    return CRYPTO_ALIASES.get(cleaned, cleaned)


def get_watchlist():
    while True:
        count = IntPrompt.ask("[bright_green]How many assets do you want to watch?[/bright_green]", default=3)
        if count > 0:
            break
        console.print("[red]Number must be greater than 0.[/red]")

    items = []

    console.print(
        Panel(
            "[cyan]Crypto examples:[/cyan] btc, bitcoin, eth, ether, sol, doge\n"
            "[cyan]Ticker examples:[/cyan] AAPL, TSLA, SPY, GLD, EURUSD=X, BTC-USD",
            title="[bright_green]INPUT FORMAT[/bright_green]",
            border_style="green",
        )
    )

    for i in range(count):
        console.print(f"\n[bold bright_green]Asset #{i + 1}[/bold bright_green]")

        while True:
            asset_type = Prompt.ask("Type", choices=["crypto", "ticker", "c", "t", "coin", "stock"], default="crypto")
            asset_type = asset_type.strip().lower()

            if asset_type in ["crypto", "c", "coin"]:
                asset_type = "crypto"
                break

            if asset_type in ["ticker", "stock", "t"]:
                asset_type = "ticker"
                break

        while True:
            symbol = Prompt.ask("ID / ticker").strip()

            if not symbol:
                console.print("[red]ID / ticker cannot be empty.[/red]")
                continue

            if asset_type == "crypto":
                symbol = resolve_crypto_id(symbol)
            else:
                symbol = symbol.upper()

            break

        items.append({
            "type": asset_type,
            "symbol": symbol,
            "last_price": None
        })

    return items


def get_crypto_price(coin_id):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": coin_id, "vs_currencies": "usd"}

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()

    data = r.json()

    if coin_id not in data or "usd" not in data[coin_id]:
        raise ValueError(f"Unknown CoinGecko crypto ID: {coin_id}")

    return float(data[coin_id]["usd"])


def get_ticker_price(ticker):
    data = yf.Ticker(ticker).history(period="1d", interval="1m")

    if data.empty:
        raise ValueError(f"No price data returned for ticker: {ticker}")

    return float(data["Close"].dropna().iloc[-1])


def get_price(item):
    if item["type"] == "crypto":
        return get_crypto_price(item["symbol"])
    return get_ticker_price(item["symbol"])


def money(value):
    return f"${value:,.6f}" if value < 1 else f"${value:,.2f}"


def build_console_table(rows):
    table = Table(title="XEVVOR LIVE MARKET DELTA", border_style="bright_green")
    table.add_column("Asset", style="bold cyan")
    table.add_column("Old Price")
    table.add_column("Current Price")
    table.add_column("$ Change")
    table.add_column("% Change")
    table.add_column("Signal")

    for row in rows:
        style = "green" if row["change"] >= 0 else "red"
        arrow = "▲ GAIN" if row["change"] >= 0 else "▼ LOSS"

        table.add_row(
            row["symbol"],
            money(row["old"]),
            money(row["new"]),
            f"[{style}]{row['change']:+,.6f}[/{style}]",
            f"[{style}]{row['pct']:+.2f}%[/{style}]",
            f"[{style}]{arrow}[/{style}]",
        )

    return table


def send_market_update(webhook, rows, ping_everyone):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    description_lines = []

    for row in rows:
        if row["change"] >= 0:
            emoji = "🟢📈"
            direction = "GAIN"
        else:
            emoji = "🔴📉"
            direction = "LOSS"

        description_lines.append(
            f"{emoji} **{row['symbol']}** `{direction}`\n"
            f"`{money(row['old'])}` → `{money(row['new'])}`\n"
            f"💰 `{row['change']:+,.6f}` | 📈 `{row['pct']:+.2f}%`\n"
        )

    content = "@everyone" if ping_everyone else None

    embed = {
        "title": "📊 XEVVOR Market Update",
        "description": "\n".join(description_lines),
        "color": 65280,
        "footer": {
            "text": "XEVVOR // market surveillance daemon"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

    payload = {
        "username": "XEVVOR Market Watch",
        "content": content,
        "embeds": [embed],
        "allowed_mentions": {
            "parse": ["everyone"] if ping_everyone else []
        }
    }

    r = requests.post(webhook, json=payload, timeout=20)
    r.raise_for_status()


def send_startup_message(webhook, ping_everyone):
    payload = {
        "username": "XEVVOR Market Watch",
        "content": "@everyone" if ping_everyone else None,
        "embeds": [
            {
                "title": "🟢 XEVVOR Online",
                "description": "```ansi\n[BOOT] Market watcher started\n[MODE] 10-minute combined embed updates\n[STATUS] Surveillance active\n```",
                "color": 65280,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ],
        "allowed_mentions": {
            "parse": ["everyone"] if ping_everyone else []
        }
    }

    requests.post(webhook, json=payload, timeout=20).raise_for_status()


def main():
    intro()

    config = load_config()
    webhook = ask_webhook(config)
    ping_everyone = ask_everyone_ping(config)
    watchlist = get_watchlist()

    console.print("\n[bright_green]Priming market feeds...[/bright_green]")

    valid_watchlist = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching initial prices...", total=None)

        for item in watchlist:
            try:
                item["last_price"] = get_price(item)
                valid_watchlist.append(item)
                console.print(f"[green]LOCKED[/green] {item['symbol']} = {money(item['last_price'])}")
            except Exception as e:
                console.print(f"[red]SKIPPED[/red] {item['symbol']}: {e}")

        progress.update(task, completed=True)

    if not valid_watchlist:
        console.print("[bold red]No valid assets to watch. Exiting.[/bold red]")
        return

    watchlist = valid_watchlist
    send_startup_message(webhook, ping_everyone)

    console.print(
        Panel.fit(
            "[bold green]DAEMON ACTIVE[/bold green]\n"
            "[cyan]Every 10 minutes, one Discord embed will be sent with all watched assets.[/cyan]",
            border_style="bright_green",
        )
    )

    while True:
        rows = []

        console.print(f"\n[bright_black]// scan started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bright_black]")

        for item in watchlist:
            try:
                old = item["last_price"]
                new = get_price(item)

                change = new - old
                pct = (change / old) * 100 if old else 0

                rows.append({
                    "symbol": item["symbol"].upper(),
                    "old": old,
                    "new": new,
                    "change": change,
                    "pct": pct,
                })

                item["last_price"] = new

            except Exception as e:
                console.print(f"[red]XEVVOR error for {item['symbol']}:[/red] {e}")

        if rows:
            console.print(build_console_table(rows))
            send_market_update(webhook, rows, ping_everyone)
            console.print("[green]Discord embed transmitted.[/green]")

        console.print(f"[bright_black]Sleeping {CHECK_INTERVAL_SECONDS // 60} minutes...[/bright_black]")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]XEVVOR stopped.[/bold red]")
        sys.exit(0)