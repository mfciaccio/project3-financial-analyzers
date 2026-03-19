# Financial Analyzers

A stock analysis tool that fetches market data and generates comprehensive financial reports.

## Features

- Fetches real-time stock data via Yahoo Finance
- Calculates technical indicators (SMA, RSI, volatility)
- Analyzes fundamental metrics (P/E, PEG, ROE, etc.)
- Tracks performance across multiple timeframes
- Generates detailed analysis reports

## Tech Stack

- Python 3
- yfinance for market data
- React frontend (optional dashboard)
- FastAPI backend (optional API)

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
pip install yfinance
```

### Usage

1. Add stock symbols to `input/stocks.csv`
2. Run the analyzer:
   ```bash
   python ciaccio/stock_analyzer.py
   ```
3. Reports saved to `output/`

## Project Structure

```
├── ciaccio/
│   ├── stock_analyzer.py   # Main analysis script
│   ├── backend/            # API server (optional)
│   └── frontend/           # Dashboard UI (optional)
├── input/                  # Input stock lists
└── output/                 # Generated reports
```

## Metrics Calculated

### Technical Indicators
- 20/50/200-day Moving Averages
- 14-day RSI
- 30-day Volatility
- Beta

### Fundamental Metrics
- P/E Ratio (trailing & forward)
- PEG Ratio
- Price-to-Book, Price-to-Sales
- Dividend Yield
- Profit Margin, ROE
- Debt-to-Equity

### Performance
- Returns: 1D, 5D, 1M, 3M, 6M, YTD, 1Y
