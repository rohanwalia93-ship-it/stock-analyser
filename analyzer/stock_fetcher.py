import yfinance as yf
import pandas as pd
from typing import Optional

# Common name → ticker symbol mapping
TICKER_MAP = {
    # Tech
    "tesla": "TSLA", "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
    "alphabet": "GOOGL", "amazon": "AMZN", "meta": "META", "facebook": "META",
    "nvidia": "NVDA", "netflix": "NFLX", "intel": "INTC", "amd": "AMD",
    "salesforce": "CRM", "adobe": "ADBE", "paypal": "PYPL", "uber": "UBER",
    "airbnb": "ABNB", "spotify": "SPOT", "twitter": "X", "x corp": "X",
    "palantir": "PLTR", "snowflake": "SNOW", "zoom": "ZM", "slack": "WORK",
    "shopify": "SHOP", "square": "SQ", "block": "SQ",
    # Finance
    "jpmorgan": "JPM", "jp morgan": "JPM", "goldman sachs": "GS",
    "bank of america": "BAC", "citigroup": "C", "wells fargo": "WFC",
    "berkshire": "BRK-B", "visa": "V", "mastercard": "MA", "amex": "AXP",
    "american express": "AXP",
    # Healthcare
    "johnson": "JNJ", "pfizer": "PFE", "moderna": "MRNA",
    "abbvie": "ABBV", "unitedhealth": "UNH", "merck": "MRK",
    # Energy
    "exxon": "XOM", "chevron": "CVX", "bp": "BP", "shell": "SHEL",
    # Consumer
    "walmart": "WMT", "target": "TGT", "costco": "COST", "nike": "NKE",
    "coca cola": "KO", "pepsi": "PEP", "mcdonalds": "MCD", "starbucks": "SBUX",
    "disney": "DIS",
    # Commodities (ETFs & Futures)
    "gold": "GC=F", "silver": "SI=F", "oil": "CL=F", "crude oil": "CL=F",
    "natural gas": "NG=F", "copper": "HG=F", "platinum": "PL=F",
    "gld": "GLD", "slv": "SLV",
    # Crypto
    "bitcoin": "BTC-USD", "btc": "BTC-USD",
    "ethereum": "ETH-USD", "eth": "ETH-USD",
    "solana": "SOL-USD", "sol": "SOL-USD",
    "cardano": "ADA-USD", "xrp": "XRP-USD",
    "dogecoin": "DOGE-USD", "doge": "DOGE-USD",
    # Indices
    "sp500": "^GSPC", "s&p": "^GSPC", "s&p 500": "^GSPC",
    "nasdaq": "^IXIC", "dow jones": "^DJI", "dow": "^DJI",
    "nifty": "^NSEI", "sensex": "^BSESN",
}

COMMODITY_TICKERS = {"GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "PL=F", "GLD", "SLV"}
CRYPTO_TICKERS_SUFFIX = "-USD"


def resolve_ticker(query: str) -> tuple[str, str]:
    """Resolve a user query to a ticker symbol and asset type.
    Returns (ticker, asset_type) where asset_type is 'stock', 'commodity', or 'crypto'.
    """
    clean = query.strip().lower()

    # Direct lookup in map
    if clean in TICKER_MAP:
        ticker = TICKER_MAP[clean]
    else:
        # Assume it might be a direct ticker symbol
        ticker = clean.upper()

    # Determine asset type
    if ticker in COMMODITY_TICKERS:
        asset_type = "commodity"
    elif ticker.endswith(CRYPTO_TICKERS_SUFFIX):
        asset_type = "crypto"
    elif ticker.startswith("^"):
        asset_type = "index"
    else:
        asset_type = "stock"

    return ticker, asset_type


def fetch_stock_data(ticker: str) -> Optional[dict]:
    """Fetch comprehensive stock data from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)

        # Get historical data (1 year)
        hist = stock.history(period="1y")
        if hist.empty:
            return None

        info = stock.info or {}

        # Latest price info
        current_price = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else current_price
        price_change = current_price - prev_close
        price_change_pct = (price_change / prev_close) * 100

        # 52-week range
        week_52_high = hist["Close"].max()
        week_52_low = hist["Close"].min()
        week_52_position = (
            (current_price - week_52_low) / (week_52_high - week_52_low) * 100
            if week_52_high != week_52_low else 50
        )

        # Volume
        avg_volume = hist["Volume"].mean()
        current_volume = hist["Volume"].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

        # Price performance
        price_1m = hist["Close"].iloc[-22] if len(hist) >= 22 else hist["Close"].iloc[0]
        price_3m = hist["Close"].iloc[-66] if len(hist) >= 66 else hist["Close"].iloc[0]
        price_6m = hist["Close"].iloc[-132] if len(hist) >= 132 else hist["Close"].iloc[0]

        return {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", "N/A"),
            "price": {
                "current": round(current_price, 2),
                "change": round(price_change, 2),
                "change_pct": round(price_change_pct, 2),
                "prev_close": round(prev_close, 2),
                "week_52_high": round(week_52_high, 2),
                "week_52_low": round(week_52_low, 2),
                "week_52_position_pct": round(week_52_position, 1),
                "return_1m_pct": round((current_price / price_1m - 1) * 100, 2),
                "return_3m_pct": round((current_price / price_3m - 1) * 100, 2),
                "return_6m_pct": round((current_price / price_6m - 1) * 100, 2),
                "return_ytd_pct": round(
                    (current_price / hist["Close"].iloc[0] - 1) * 100, 2
                ),
            },
            "volume": {
                "current": int(current_volume),
                "avg_30d": int(avg_volume),
                "ratio": round(volume_ratio, 2),
            },
            "fundamentals": _extract_fundamentals(info),
            "history": hist,
        }
    except Exception as e:
        return {"error": str(e)}


def _extract_fundamentals(info: dict) -> dict:
    """Extract fundamental metrics from yfinance info dict."""
    def safe_get(key, default=None):
        val = info.get(key)
        if val in (None, "N/A", float("inf"), float("-inf")):
            return default
        try:
            return round(float(val), 2)
        except (TypeError, ValueError):
            return val

    def fmt_large(val):
        if val is None:
            return "N/A"
        val = float(val)
        if abs(val) >= 1e12:
            return f"${val/1e12:.2f}T"
        if abs(val) >= 1e9:
            return f"${val/1e9:.2f}B"
        if abs(val) >= 1e6:
            return f"${val/1e6:.2f}M"
        return f"${val:,.0f}"

    return {
        # Valuation
        "market_cap": fmt_large(info.get("marketCap")),
        "pe_ratio": safe_get("trailingPE"),
        "forward_pe": safe_get("forwardPE"),
        "pb_ratio": safe_get("priceToBook"),
        "ps_ratio": safe_get("priceToSalesTrailing12Months"),
        "ev_ebitda": safe_get("enterpriseToEbitda"),
        "peg_ratio": safe_get("pegRatio"),
        # Profitability
        "eps_ttm": safe_get("trailingEps"),
        "eps_forward": safe_get("forwardEps"),
        "profit_margin": safe_get("profitMargins"),
        "operating_margin": safe_get("operatingMargins"),
        "roe": safe_get("returnOnEquity"),
        "roa": safe_get("returnOnAssets"),
        # Growth
        "revenue_growth_yoy": safe_get("revenueGrowth"),
        "earnings_growth_yoy": safe_get("earningsGrowth"),
        "revenue_ttm": fmt_large(info.get("totalRevenue")),
        # Balance sheet
        "debt_to_equity": safe_get("debtToEquity"),
        "current_ratio": safe_get("currentRatio"),
        "quick_ratio": safe_get("quickRatio"),
        "free_cash_flow": fmt_large(info.get("freeCashflow")),
        # Dividends
        "dividend_yield": safe_get("dividendYield"),
        "payout_ratio": safe_get("payoutRatio"),
        # Analyst
        "analyst_target": safe_get("targetMeanPrice"),
        "analyst_recommendation": info.get("recommendationKey", "N/A"),
        "analyst_count": info.get("numberOfAnalystOpinions"),
        "beta": safe_get("beta"),
    }
