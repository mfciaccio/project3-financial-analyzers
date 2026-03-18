#!/usr/bin/env python3
"""
Stock Analyzer - Financial Analysis Tool
Analyzes stocks from input CSV and generates comprehensive reports.
"""

import csv
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import statistics

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("Warning: yfinance not installed. Run: pip install yfinance")


@dataclass
class StockInfo:
    symbol: str
    company_name: str
    sector: str
    industry: str


@dataclass
class PriceData:
    current_price: float
    open_price: float
    high_52week: float
    low_52week: float
    previous_close: float
    volume: int
    avg_volume: int
    market_cap: Optional[float]


@dataclass
class TechnicalIndicators:
    sma_20: Optional[float]  # 20-day Simple Moving Average
    sma_50: Optional[float]  # 50-day Simple Moving Average
    sma_200: Optional[float]  # 200-day Simple Moving Average
    rsi_14: Optional[float]  # 14-day Relative Strength Index
    volatility_30d: Optional[float]  # 30-day volatility (std dev of returns)
    beta: Optional[float]
    price_to_sma20: Optional[float]  # Current price vs SMA20 (%)
    price_to_sma50: Optional[float]  # Current price vs SMA50 (%)


@dataclass
class FundamentalMetrics:
    pe_ratio: Optional[float]
    forward_pe: Optional[float]
    peg_ratio: Optional[float]
    price_to_book: Optional[float]
    price_to_sales: Optional[float]
    dividend_yield: Optional[float]
    profit_margin: Optional[float]
    return_on_equity: Optional[float]
    debt_to_equity: Optional[float]
    earnings_growth: Optional[float]
    revenue_growth: Optional[float]


@dataclass
class PerformanceMetrics:
    return_1d: Optional[float]
    return_5d: Optional[float]
    return_1m: Optional[float]
    return_3m: Optional[float]
    return_6m: Optional[float]
    return_ytd: Optional[float]
    return_1y: Optional[float]


@dataclass
class AnalysisResult:
    symbol: str
    company_name: str
    sector: str
    industry: str
    analysis_date: str
    price_data: Optional[PriceData]
    technical: Optional[TechnicalIndicators]
    fundamentals: Optional[FundamentalMetrics]
    performance: Optional[PerformanceMetrics]
    recommendation: str
    risk_level: str
    analysis_summary: str
    error: Optional[str] = None


def load_stock_symbols(csv_path: str) -> List[StockInfo]:
    """Load stock symbols from CSV file."""
    stocks = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stocks.append(StockInfo(
                symbol=row['Symbol'],
                company_name=row['Company Name'],
                sector=row['Sector'],
                industry=row['Industry']
            ))
    return stocks


def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return None
    return statistics.mean(prices[-period:])


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """Calculate Relative Strength Index."""
    if len(prices) < period + 1:
        return None

    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [c if c > 0 else 0 for c in changes[-period:]]
    losses = [-c if c < 0 else 0 for c in changes[-period:]]

    avg_gain = statistics.mean(gains) if gains else 0
    avg_loss = statistics.mean(losses) if losses else 0

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)


def calculate_volatility(prices: List[float], period: int = 30) -> Optional[float]:
    """Calculate annualized volatility from daily returns."""
    if len(prices) < period + 1:
        return None

    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    recent_returns = returns[-period:]

    if len(recent_returns) < 2:
        return None

    daily_vol = statistics.stdev(recent_returns)
    annual_vol = daily_vol * (252 ** 0.5)  # Annualize
    return round(annual_vol * 100, 2)  # As percentage


def calculate_returns(prices: List[float], current: float, periods: Dict[str, int]) -> Dict[str, Optional[float]]:
    """Calculate returns over various periods."""
    results = {}
    for name, days in periods.items():
        if len(prices) >= days:
            past_price = prices[-days]
            ret = ((current - past_price) / past_price) * 100
            results[name] = round(ret, 2)
        else:
            results[name] = None
    return results


def analyze_stock(stock_info: StockInfo) -> AnalysisResult:
    """Perform comprehensive analysis on a single stock."""

    if not YFINANCE_AVAILABLE:
        return AnalysisResult(
            symbol=stock_info.symbol,
            company_name=stock_info.company_name,
            sector=stock_info.sector,
            industry=stock_info.industry,
            analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            price_data=None,
            technical=None,
            fundamentals=None,
            performance=None,
            recommendation="N/A",
            risk_level="N/A",
            analysis_summary="yfinance library not available",
            error="yfinance not installed"
        )

    try:
        ticker = yf.Ticker(stock_info.symbol)
        info = ticker.info

        # Get historical data (1 year)
        hist = ticker.history(period="1y")
        if hist.empty:
            raise ValueError("No historical data available")

        prices = hist['Close'].tolist()
        current_price = prices[-1] if prices else 0

        # Price Data
        price_data = PriceData(
            current_price=round(current_price, 2),
            open_price=round(info.get('open', info.get('regularMarketOpen', 0)), 2),
            high_52week=round(info.get('fiftyTwoWeekHigh', 0), 2),
            low_52week=round(info.get('fiftyTwoWeekLow', 0), 2),
            previous_close=round(info.get('previousClose', info.get('regularMarketPreviousClose', 0)), 2),
            volume=info.get('volume', info.get('regularMarketVolume', 0)),
            avg_volume=info.get('averageVolume', 0),
            market_cap=info.get('marketCap')
        )

        # Technical Indicators
        sma_20 = calculate_sma(prices, 20)
        sma_50 = calculate_sma(prices, 50)
        sma_200 = calculate_sma(prices, 200)

        technical = TechnicalIndicators(
            sma_20=round(sma_20, 2) if sma_20 else None,
            sma_50=round(sma_50, 2) if sma_50 else None,
            sma_200=round(sma_200, 2) if sma_200 else None,
            rsi_14=calculate_rsi(prices, 14),
            volatility_30d=calculate_volatility(prices, 30),
            beta=info.get('beta'),
            price_to_sma20=round(((current_price - sma_20) / sma_20) * 100, 2) if sma_20 else None,
            price_to_sma50=round(((current_price - sma_50) / sma_50) * 100, 2) if sma_50 else None
        )

        # Fundamental Metrics
        fundamentals = FundamentalMetrics(
            pe_ratio=info.get('trailingPE'),
            forward_pe=info.get('forwardPE'),
            peg_ratio=info.get('pegRatio'),
            price_to_book=info.get('priceToBook'),
            price_to_sales=info.get('priceToSalesTrailing12Months'),
            dividend_yield=round(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else None,
            profit_margin=round(info.get('profitMargins', 0) * 100, 2) if info.get('profitMargins') else None,
            return_on_equity=round(info.get('returnOnEquity', 0) * 100, 2) if info.get('returnOnEquity') else None,
            debt_to_equity=info.get('debtToEquity'),
            earnings_growth=round(info.get('earningsGrowth', 0) * 100, 2) if info.get('earningsGrowth') else None,
            revenue_growth=round(info.get('revenueGrowth', 0) * 100, 2) if info.get('revenueGrowth') else None
        )

        # Performance Metrics
        return_periods = {'1d': 1, '5d': 5, '1m': 21, '3m': 63, '6m': 126, '1y': 252}
        returns = calculate_returns(prices, current_price, return_periods)

        # YTD calculation
        year_start = datetime(datetime.now().year, 1, 1)
        ytd_hist = ticker.history(start=year_start)
        ytd_return = None
        if not ytd_hist.empty:
            ytd_start_price = ytd_hist['Close'].iloc[0]
            ytd_return = round(((current_price - ytd_start_price) / ytd_start_price) * 100, 2)

        performance = PerformanceMetrics(
            return_1d=returns.get('1d'),
            return_5d=returns.get('5d'),
            return_1m=returns.get('1m'),
            return_3m=returns.get('3m'),
            return_6m=returns.get('6m'),
            return_ytd=ytd_return,
            return_1y=returns.get('1y')
        )

        # Generate recommendation
        recommendation, risk_level, summary = generate_recommendation(
            price_data, technical, fundamentals, performance, stock_info
        )

        return AnalysisResult(
            symbol=stock_info.symbol,
            company_name=stock_info.company_name,
            sector=stock_info.sector,
            industry=stock_info.industry,
            analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            price_data=price_data,
            technical=technical,
            fundamentals=fundamentals,
            performance=performance,
            recommendation=recommendation,
            risk_level=risk_level,
            analysis_summary=summary
        )

    except Exception as e:
        return AnalysisResult(
            symbol=stock_info.symbol,
            company_name=stock_info.company_name,
            sector=stock_info.sector,
            industry=stock_info.industry,
            analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            price_data=None,
            technical=None,
            fundamentals=None,
            performance=None,
            recommendation="N/A",
            risk_level="N/A",
            analysis_summary=f"Analysis failed: {str(e)}",
            error=str(e)
        )


def generate_recommendation(
    price: PriceData,
    tech: TechnicalIndicators,
    fund: FundamentalMetrics,
    perf: PerformanceMetrics,
    info: StockInfo
) -> tuple:
    """Generate investment recommendation based on analysis."""

    signals = {'bullish': 0, 'bearish': 0, 'neutral': 0}
    risk_factors = []
    summary_points = []

    # Technical Analysis Signals
    if tech.rsi_14:
        if tech.rsi_14 < 30:
            signals['bullish'] += 2
            summary_points.append("RSI indicates oversold conditions")
        elif tech.rsi_14 > 70:
            signals['bearish'] += 2
            summary_points.append("RSI indicates overbought conditions")
        else:
            signals['neutral'] += 1

    if tech.price_to_sma50:
        if tech.price_to_sma50 > 5:
            signals['bullish'] += 1
            summary_points.append("Trading above 50-day SMA")
        elif tech.price_to_sma50 < -5:
            signals['bearish'] += 1
            summary_points.append("Trading below 50-day SMA")

    if tech.sma_50 and tech.sma_200:
        if tech.sma_50 > tech.sma_200:
            signals['bullish'] += 1
            summary_points.append("Golden cross pattern (50 SMA > 200 SMA)")
        else:
            signals['bearish'] += 1
            summary_points.append("Death cross pattern (50 SMA < 200 SMA)")

    # Volatility Assessment
    if tech.volatility_30d:
        if tech.volatility_30d > 40:
            risk_factors.append("High volatility")
        elif tech.volatility_30d > 25:
            risk_factors.append("Moderate volatility")

    if tech.beta:
        if tech.beta > 1.5:
            risk_factors.append("High beta (more volatile than market)")
        elif tech.beta < 0.5:
            summary_points.append("Low beta (defensive stock)")

    # Fundamental Analysis Signals
    if fund.pe_ratio:
        if fund.pe_ratio < 15:
            signals['bullish'] += 1
            summary_points.append("Attractive P/E ratio")
        elif fund.pe_ratio > 30:
            signals['bearish'] += 1
            risk_factors.append("High P/E ratio")

    if fund.peg_ratio:
        if fund.peg_ratio < 1:
            signals['bullish'] += 1
            summary_points.append("PEG ratio suggests undervaluation")
        elif fund.peg_ratio > 2:
            signals['bearish'] += 1

    if fund.dividend_yield and fund.dividend_yield > 2:
        signals['bullish'] += 1
        summary_points.append(f"Attractive dividend yield ({fund.dividend_yield}%)")

    if fund.debt_to_equity and fund.debt_to_equity > 100:
        risk_factors.append("High debt-to-equity ratio")

    if fund.profit_margin and fund.profit_margin > 20:
        signals['bullish'] += 1
        summary_points.append("Strong profit margins")

    # Performance Signals
    if perf.return_1y:
        if perf.return_1y > 20:
            signals['bullish'] += 1
            summary_points.append(f"Strong 1-year return ({perf.return_1y}%)")
        elif perf.return_1y < -20:
            signals['bearish'] += 1
            risk_factors.append(f"Weak 1-year return ({perf.return_1y}%)")

    # Determine recommendation
    total_signals = signals['bullish'] + signals['bearish'] + signals['neutral']
    if total_signals == 0:
        recommendation = "HOLD"
    elif signals['bullish'] > signals['bearish'] + 2:
        recommendation = "STRONG BUY"
    elif signals['bullish'] > signals['bearish']:
        recommendation = "BUY"
    elif signals['bearish'] > signals['bullish'] + 2:
        recommendation = "STRONG SELL"
    elif signals['bearish'] > signals['bullish']:
        recommendation = "SELL"
    else:
        recommendation = "HOLD"

    # Determine risk level
    risk_count = len(risk_factors)
    if risk_count >= 3:
        risk_level = "HIGH"
    elif risk_count >= 1:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    # Build summary
    summary = f"{info.company_name} ({info.symbol}) - {info.sector}. "
    if summary_points:
        summary += " ".join(summary_points[:3]) + ". "
    if risk_factors:
        summary += "Risk factors: " + ", ".join(risk_factors[:2]) + "."

    return recommendation, risk_level, summary


def generate_csv_report(results: List[AnalysisResult], output_path: str):
    """Generate CSV summary report."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Symbol', 'Company', 'Sector', 'Industry',
            'Current Price', 'Market Cap (B)', '52W High', '52W Low',
            'P/E Ratio', 'Forward P/E', 'PEG Ratio', 'Dividend Yield %',
            'RSI (14)', '30D Volatility %', 'Beta',
            'Return 1D %', 'Return 1M %', 'Return YTD %', 'Return 1Y %',
            'Recommendation', 'Risk Level', 'Summary'
        ])

        for r in results:
            if r.error:
                writer.writerow([r.symbol, r.company_name, r.sector, r.industry] + ['N/A'] * 15 + [r.error])
                continue

            price = r.price_data
            tech = r.technical
            fund = r.fundamentals
            perf = r.performance

            market_cap_b = round(price.market_cap / 1e9, 2) if price.market_cap else 'N/A'

            writer.writerow([
                r.symbol, r.company_name, r.sector, r.industry,
                price.current_price, market_cap_b, price.high_52week, price.low_52week,
                fund.pe_ratio or 'N/A', fund.forward_pe or 'N/A', fund.peg_ratio or 'N/A', fund.dividend_yield or 'N/A',
                tech.rsi_14 or 'N/A', tech.volatility_30d or 'N/A', tech.beta or 'N/A',
                perf.return_1d or 'N/A', perf.return_1m or 'N/A', perf.return_ytd or 'N/A', perf.return_1y or 'N/A',
                r.recommendation, r.risk_level, r.analysis_summary[:100]
            ])


def generate_detailed_report(results: List[AnalysisResult], output_path: str):
    """Generate detailed text report."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("STOCK ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        # Summary by recommendation
        recommendations = {}
        for r in results:
            rec = r.recommendation
            if rec not in recommendations:
                recommendations[rec] = []
            recommendations[rec].append(r.symbol)

        f.write("RECOMMENDATION SUMMARY\n")
        f.write("-" * 40 + "\n")
        for rec in ['STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL', 'N/A']:
            if rec in recommendations:
                f.write(f"{rec}: {', '.join(recommendations[rec])}\n")
        f.write("\n")

        # Sector breakdown
        sectors = {}
        for r in results:
            if r.sector not in sectors:
                sectors[r.sector] = []
            sectors[r.sector].append(r)

        f.write("SECTOR BREAKDOWN\n")
        f.write("-" * 40 + "\n")
        for sector, stocks in sorted(sectors.items()):
            f.write(f"\n{sector} ({len(stocks)} stocks)\n")
            for r in stocks:
                if r.price_data:
                    f.write(f"  {r.symbol:6} ${r.price_data.current_price:>10.2f}  {r.recommendation:12} {r.risk_level:10}\n")
                else:
                    f.write(f"  {r.symbol:6} {'N/A':>11}  {r.recommendation:12} {r.risk_level:10}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("DETAILED ANALYSIS\n")
        f.write("=" * 80 + "\n\n")

        for r in results:
            f.write(f"\n{'='*60}\n")
            f.write(f"{r.symbol} - {r.company_name}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Sector: {r.sector} | Industry: {r.industry}\n")
            f.write(f"Analysis Date: {r.analysis_date}\n\n")

            if r.error:
                f.write(f"ERROR: {r.error}\n")
                continue

            # Price Data
            p = r.price_data
            f.write("PRICE DATA\n")
            f.write(f"  Current Price: ${p.current_price:,.2f}\n")
            f.write(f"  52-Week Range: ${p.low_52week:,.2f} - ${p.high_52week:,.2f}\n")
            f.write(f"  Volume: {p.volume:,} (Avg: {p.avg_volume:,})\n")
            if p.market_cap:
                f.write(f"  Market Cap: ${p.market_cap/1e9:,.2f}B\n")
            f.write("\n")

            # Technical
            t = r.technical
            f.write("TECHNICAL INDICATORS\n")
            f.write(f"  SMA 20/50/200: {t.sma_20 or 'N/A'} / {t.sma_50 or 'N/A'} / {t.sma_200 or 'N/A'}\n")
            f.write(f"  RSI (14): {t.rsi_14 or 'N/A'}\n")
            f.write(f"  30-Day Volatility: {t.volatility_30d or 'N/A'}%\n")
            f.write(f"  Beta: {t.beta or 'N/A'}\n")
            f.write("\n")

            # Fundamentals
            fu = r.fundamentals
            f.write("FUNDAMENTALS\n")
            f.write(f"  P/E Ratio: {fu.pe_ratio or 'N/A'} (Forward: {fu.forward_pe or 'N/A'})\n")
            f.write(f"  PEG Ratio: {fu.peg_ratio or 'N/A'}\n")
            f.write(f"  P/B Ratio: {fu.price_to_book or 'N/A'}\n")
            f.write(f"  Dividend Yield: {fu.dividend_yield or 'N/A'}%\n")
            f.write(f"  Profit Margin: {fu.profit_margin or 'N/A'}%\n")
            f.write(f"  ROE: {fu.return_on_equity or 'N/A'}%\n")
            f.write(f"  D/E Ratio: {fu.debt_to_equity or 'N/A'}\n")
            f.write("\n")

            # Performance
            pe = r.performance
            f.write("PERFORMANCE\n")
            f.write(f"  1D: {pe.return_1d or 'N/A'}% | 5D: {pe.return_5d or 'N/A'}% | 1M: {pe.return_1m or 'N/A'}%\n")
            f.write(f"  3M: {pe.return_3m or 'N/A'}% | 6M: {pe.return_6m or 'N/A'}% | YTD: {pe.return_ytd or 'N/A'}%\n")
            f.write(f"  1Y: {pe.return_1y or 'N/A'}%\n")
            f.write("\n")

            # Recommendation
            f.write("RECOMMENDATION\n")
            f.write(f"  Rating: {r.recommendation}\n")
            f.write(f"  Risk Level: {r.risk_level}\n")
            f.write(f"  Summary: {r.analysis_summary}\n")


def generate_json_report(results: List[AnalysisResult], output_path: str):
    """Generate JSON report for programmatic access."""

    def convert_dataclass(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        return obj

    data = {
        'report_date': datetime.now().isoformat(),
        'total_stocks': len(results),
        'results': [asdict(r) for r in results]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def main():
    """Main function to run stock analysis."""

    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / 'input'
    output_dir = base_dir / 'output'

    output_dir.mkdir(exist_ok=True)

    # Load stock symbols
    symbols_path = input_dir / 'stock_symbols.csv'
    print(f"Loading stock symbols from {symbols_path}...")
    stocks = load_stock_symbols(symbols_path)
    print(f"Loaded {len(stocks)} stocks for analysis\n")

    if not YFINANCE_AVAILABLE:
        print("ERROR: yfinance is required for stock analysis.")
        print("Install with: pip install yfinance")
        return

    # Analyze each stock
    results = []
    for i, stock in enumerate(stocks, 1):
        print(f"[{i}/{len(stocks)}] Analyzing {stock.symbol} ({stock.company_name})...")
        result = analyze_stock(stock)
        results.append(result)

        if result.error:
            print(f"         ERROR: {result.error}")
        else:
            print(f"         ${result.price_data.current_price:,.2f} | {result.recommendation} | {result.risk_level} risk")

    # Generate reports
    print("\nGenerating reports...")

    csv_path = output_dir / 'stock_analysis_summary.csv'
    generate_csv_report(results, csv_path)
    print(f"  CSV report: {csv_path}")

    txt_path = output_dir / 'stock_analysis_detailed.txt'
    generate_detailed_report(results, txt_path)
    print(f"  Detailed report: {txt_path}")

    json_path = output_dir / 'stock_analysis_data.json'
    generate_json_report(results, json_path)
    print(f"  JSON data: {json_path}")

    # Print summary
    print("\n" + "=" * 50)
    print("ANALYSIS COMPLETE")
    print("=" * 50)

    buy_signals = [r for r in results if 'BUY' in r.recommendation]
    sell_signals = [r for r in results if 'SELL' in r.recommendation]
    hold_signals = [r for r in results if r.recommendation == 'HOLD']

    print(f"  Buy signals: {len(buy_signals)}")
    print(f"  Hold signals: {len(hold_signals)}")
    print(f"  Sell signals: {len(sell_signals)}")

    if buy_signals:
        print(f"\n  Top picks: {', '.join([r.symbol for r in buy_signals[:5]])}")


if __name__ == '__main__':
    main()
