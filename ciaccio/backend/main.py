#!/usr/bin/env python3
"""
Stock Recommendation API - FastAPI Backend
Provides stock analysis, news, and buy/sell/hold recommendations.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

app = FastAPI(
    title="Stock Recommendation API",
    description="API for stock analysis and recommendations",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class StockSymbol(BaseModel):
    symbol: str
    company_name: str
    sector: str
    industry: str


class NewsItem(BaseModel):
    title: str
    source: str
    published: str
    summary: str
    sentiment: str  # positive, negative, neutral
    url: Optional[str] = None


class StockPrice(BaseModel):
    current: float
    change: float
    change_percent: float
    high: float
    low: float
    open: float
    previous_close: float
    volume: int


class Recommendation(BaseModel):
    action: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    reasoning: List[str]
    risk_level: str  # LOW, MODERATE, HIGH
    price_target: Optional[float] = None
    time_horizon: str  # short-term, medium-term, long-term


class StockAnalysis(BaseModel):
    symbol: str
    company_name: str
    sector: str
    industry: str
    price: StockPrice
    news: List[NewsItem]
    recommendation: Recommendation
    analysis_date: str


# Load stock symbols
def load_symbols() -> List[StockSymbol]:
    """Load stock symbols from CSV."""
    symbols = []
    csv_path = Path(__file__).parent.parent.parent / 'input' / 'stock_symbols.csv'

    if csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbols.append(StockSymbol(
                    symbol=row['Symbol'],
                    company_name=row['Company Name'],
                    sector=row['Sector'],
                    industry=row['Industry']
                ))
    return symbols


STOCK_SYMBOLS = load_symbols()


def get_stock_info(symbol: str) -> Optional[StockSymbol]:
    """Get stock info by symbol."""
    for stock in STOCK_SYMBOLS:
        if stock.symbol == symbol.upper():
            return stock
    return None


def fetch_real_price(symbol: str) -> Optional[StockPrice]:
    """Fetch real price data using yfinance."""
    if not YFINANCE_AVAILABLE:
        return None

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        current = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        previous = info.get('previousClose', info.get('regularMarketPreviousClose', current))

        change = current - previous
        change_pct = (change / previous * 100) if previous else 0

        return StockPrice(
            current=round(current, 2),
            change=round(change, 2),
            change_percent=round(change_pct, 2),
            high=round(info.get('dayHigh', info.get('regularMarketDayHigh', current)), 2),
            low=round(info.get('dayLow', info.get('regularMarketDayLow', current)), 2),
            open=round(info.get('open', info.get('regularMarketOpen', current)), 2),
            previous_close=round(previous, 2),
            volume=info.get('volume', info.get('regularMarketVolume', 0))
        )
    except Exception:
        return None


def generate_synthetic_price(symbol: str) -> StockPrice:
    """Generate synthetic price data for demo purposes."""
    random.seed(hash(symbol) % 1000)  # Consistent per symbol

    base_prices = {
        'AAPL': 185, 'MSFT': 420, 'GOOGL': 175, 'AMZN': 185, 'NVDA': 880,
        'META': 500, 'TSLA': 175, 'JPM': 195, 'V': 280, 'JNJ': 155,
        'XOM': 115, 'PG': 165, 'KO': 62, 'PEP': 175, 'WMT': 165,
    }

    base = base_prices.get(symbol, random.uniform(50, 500))
    current = base * random.uniform(0.95, 1.05)
    change = random.uniform(-5, 5)

    return StockPrice(
        current=round(current, 2),
        change=round(change, 2),
        change_percent=round(change / current * 100, 2),
        high=round(current * 1.02, 2),
        low=round(current * 0.98, 2),
        open=round(current - change / 2, 2),
        previous_close=round(current - change, 2),
        volume=random.randint(10000000, 100000000)
    )


def generate_news(symbol: str, company_name: str, sector: str) -> List[NewsItem]:
    """Generate synthetic news for demonstration."""
    random.seed(hash(symbol + str(datetime.now().date())) % 10000)

    news_templates = {
        'positive': [
            (f"{company_name} Beats Q4 Earnings Expectations", "Strong revenue growth driven by new product launches and market expansion."),
            (f"Analysts Upgrade {symbol} to Buy Rating", "Multiple Wall Street analysts raise price targets citing strong fundamentals."),
            (f"{company_name} Announces Strategic Partnership", "New partnership expected to drive significant growth in emerging markets."),
            (f"{symbol} Reports Record Revenue Quarter", "Company exceeds analyst expectations with strong performance across all segments."),
            (f"Institutional Investors Increase {symbol} Holdings", "Major funds show confidence with significant position increases."),
        ],
        'negative': [
            (f"{company_name} Misses Revenue Targets", "Quarterly results fall short of analyst expectations amid challenging market conditions."),
            (f"Analysts Downgrade {symbol} Citing Growth Concerns", "Slowing growth and competitive pressures lead to cautious outlook."),
            (f"{company_name} Faces Regulatory Scrutiny", "New investigation could impact future operations and profitability."),
            (f"{symbol} Announces Workforce Reduction", "Cost-cutting measures signal potential headwinds for the company."),
            (f"Supply Chain Issues Impact {company_name}", "Ongoing disruptions expected to affect near-term performance."),
        ],
        'neutral': [
            (f"{company_name} Maintains Dividend", "Board approves quarterly dividend in line with expectations."),
            (f"{symbol} Trading in Line with Sector", f"{sector} stocks show mixed performance amid market volatility."),
            (f"{company_name} Hosts Annual Investor Day", "Management outlines strategy with focus on long-term growth initiatives."),
            (f"Market Watch: {symbol} Technical Analysis", "Stock consolidates near key support levels as traders await catalysts."),
        ]
    }

    sources = ["Bloomberg", "Reuters", "CNBC", "Wall Street Journal", "MarketWatch", "Financial Times", "Yahoo Finance"]

    news_items = []

    # Generate 3-5 news items with mixed sentiment
    sentiment_distribution = random.choices(
        ['positive', 'negative', 'neutral'],
        weights=[0.4, 0.3, 0.3],
        k=random.randint(3, 5)
    )

    for i, sentiment in enumerate(sentiment_distribution):
        templates = news_templates[sentiment]
        title, summary = random.choice(templates)

        days_ago = random.randint(0, 7)
        pub_date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))

        news_items.append(NewsItem(
            title=title,
            source=random.choice(sources),
            published=pub_date.strftime("%Y-%m-%d %H:%M"),
            summary=summary,
            sentiment=sentiment
        ))

    # Sort by date (most recent first)
    news_items.sort(key=lambda x: x.published, reverse=True)
    return news_items


def generate_recommendation(symbol: str, price: StockPrice, news: List[NewsItem], sector: str) -> Recommendation:
    """Generate investment recommendation based on analysis."""

    reasoning = []
    score = 50  # Start neutral

    # Analyze news sentiment
    positive_news = sum(1 for n in news if n.sentiment == 'positive')
    negative_news = sum(1 for n in news if n.sentiment == 'negative')

    if positive_news > negative_news:
        score += 15 * (positive_news - negative_news)
        reasoning.append(f"Positive news sentiment ({positive_news} positive vs {negative_news} negative articles)")
    elif negative_news > positive_news:
        score -= 15 * (negative_news - positive_news)
        reasoning.append(f"Negative news sentiment ({negative_news} negative vs {positive_news} positive articles)")
    else:
        reasoning.append("Mixed news sentiment suggests market uncertainty")

    # Price momentum
    if price.change_percent > 2:
        score += 10
        reasoning.append(f"Strong positive momentum (+{price.change_percent}% today)")
    elif price.change_percent > 0:
        score += 5
        reasoning.append(f"Positive price action (+{price.change_percent}% today)")
    elif price.change_percent < -2:
        score -= 10
        reasoning.append(f"Significant price decline ({price.change_percent}% today)")
    elif price.change_percent < 0:
        score -= 5
        reasoning.append(f"Minor price weakness ({price.change_percent}% today)")

    # Volume analysis
    random.seed(hash(symbol + "vol"))
    avg_volume = price.volume * random.uniform(0.8, 1.2)
    volume_ratio = price.volume / avg_volume if avg_volume else 1

    if volume_ratio > 1.5:
        reasoning.append("High trading volume indicates strong investor interest")
        score += 5 if price.change > 0 else -5
    elif volume_ratio < 0.7:
        reasoning.append("Below-average volume suggests low conviction in current move")

    # Sector considerations
    growth_sectors = ['Technology', 'Consumer Cyclical', 'Communication Services']
    defensive_sectors = ['Consumer Defensive', 'Healthcare', 'Utilities']

    if sector in growth_sectors:
        reasoning.append(f"{sector} sector typically offers higher growth potential but with increased volatility")
    elif sector in defensive_sectors:
        reasoning.append(f"{sector} sector provides stability and often performs well in uncertain markets")
        score += 5

    # Determine recommendation
    if score >= 70:
        action = "BUY"
        confidence = min(95, 60 + (score - 70))
        risk = "MODERATE" if sector in growth_sectors else "LOW"
        time_horizon = "medium-term"
    elif score >= 55:
        action = "BUY"
        confidence = 55 + (score - 55)
        risk = "MODERATE"
        time_horizon = "medium-term"
    elif score >= 45:
        action = "HOLD"
        confidence = 50 + abs(score - 50)
        risk = "MODERATE"
        time_horizon = "short-term"
        reasoning.append("Wait for clearer signals before making significant moves")
    elif score >= 30:
        action = "SELL"
        confidence = 55 + (45 - score)
        risk = "MODERATE" if sector in defensive_sectors else "HIGH"
        time_horizon = "short-term"
    else:
        action = "SELL"
        confidence = min(90, 70 + (30 - score))
        risk = "HIGH"
        time_horizon = "immediate"
        reasoning.append("Consider reducing position to manage risk")

    # Calculate price target
    if action == "BUY":
        target = price.current * random.uniform(1.08, 1.20)
    elif action == "SELL":
        target = price.current * random.uniform(0.85, 0.95)
    else:
        target = price.current * random.uniform(0.98, 1.05)

    return Recommendation(
        action=action,
        confidence=round(confidence, 1),
        reasoning=reasoning,
        risk_level=risk,
        price_target=round(target, 2),
        time_horizon=time_horizon
    )


# API Endpoints
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Stock Recommendation API",
        "version": "1.0.0",
        "endpoints": ["/stocks", "/analyze/{symbol}"]
    }


@app.get("/stocks", response_model=List[StockSymbol])
async def get_stocks():
    """Get all available stock symbols."""
    return STOCK_SYMBOLS


@app.get("/stocks/sectors")
async def get_sectors():
    """Get unique sectors."""
    sectors = list(set(s.sector for s in STOCK_SYMBOLS))
    return sorted(sectors)


@app.get("/analyze/{symbol}", response_model=StockAnalysis)
async def analyze_stock(symbol: str):
    """Get complete analysis and recommendation for a stock."""
    symbol = symbol.upper()

    stock_info = get_stock_info(symbol)
    if not stock_info:
        raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found")

    # Try to get real price data, fall back to synthetic
    price = fetch_real_price(symbol)
    if not price:
        price = generate_synthetic_price(symbol)

    # Generate news (synthetic for demo)
    news = generate_news(symbol, stock_info.company_name, stock_info.sector)

    # Generate recommendation
    recommendation = generate_recommendation(symbol, price, news, stock_info.sector)

    return StockAnalysis(
        symbol=symbol,
        company_name=stock_info.company_name,
        sector=stock_info.sector,
        industry=stock_info.industry,
        price=price,
        news=news,
        recommendation=recommendation,
        analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "yfinance_available": YFINANCE_AVAILABLE,
        "stocks_loaded": len(STOCK_SYMBOLS)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
