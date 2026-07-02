# XEVVOR Market Watch

A simple Python application that monitors cryptocurrencies and other market assets, then sends updates to a Discord webhook every 10 minutes.

The project currently supports cryptocurrencies through CoinGecko and stocks, ETFs and other tickers through Yahoo Finance.

## Features

- Monitor multiple assets at once
- Supports cryptocurrencies and market tickers
- Discord webhook notifications
- Optional `@everyone` ping
- Combined market update every 10 minutes
- Price difference in dollars
- Percentage change
- Current price
- Timestamp on every update
- Saves your webhook for future runs
- Supports common crypto aliases (`btc`, `eth`, `sol`, `doge`, etc.)

## Installation

Clone the repository.

```bash
git clone https://github.com/YOUR_USERNAME/xevvor-market-watch.git
cd xevvor-market-watch
```

Create a virtual environment.

```bash
python3 -m venv .venv
```

Activate it.

Linux/macOS

```bash
source .venv/bin/activate
```

Windows

```powershell
.venv\Scripts\activate
```

Install the dependencies.

```bash
pip install -r requirements.txt
```

Run the program.

```bash
python xevvor_watch.py
```

## Configuration

The first time you start the application you'll be asked for:

- Discord webhook URL
- Whether to ping `@everyone`
- Assets to monitor

Your webhook and settings are stored locally in `xevvor_config.json`.

## Supported inputs

Cryptocurrencies can be entered using common names or abbreviations.

Examples:

```
btc
bitcoin

eth
ether
ethereum

sol
solana

doge
dogecoin

avax
matic
bnb
xrp
ada
```

For stocks and other assets, enter the Yahoo Finance ticker.

Examples:

```
AAPL
TSLA
MSFT
SPY
GLD
BTC-USD
EURUSD=X
```

## Dependencies

- requests
- rich
- yfinance

## License

MIT