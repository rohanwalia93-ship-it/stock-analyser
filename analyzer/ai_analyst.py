import os
import anthropic
from .technical import compute_technical_indicators


def analyze_stock(stock_data: dict, asset_type: str) -> str:
    """Use Claude claude-opus-4-7 to analyze stock data and generate a recommendation."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    hist = stock_data.pop("history", None)
    tech = {}
    if hist is not None and not hist.empty:
        tech = compute_technical_indicators(hist)
    stock_data["technical"] = tech

    prompt = _build_analysis_prompt(stock_data, asset_type)

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=_system_prompt(),
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract text from response (thinking blocks come first, skip them)
    for block in response.content:
        if block.type == "text":
            return block.text.strip()

    return "Analysis unavailable."


def _system_prompt() -> str:
    return """You are an expert stock market analyst and financial advisor with 20+ years of experience.

Your job is to analyze stocks, commodities, and crypto assets and give clear, actionable recommendations.

Format your response EXACTLY as follows (use emojis exactly as shown):

📊 *[TICKER] - [COMPANY NAME]*
💰 Price: $[price] ([change]%)

📈 *FUNDAMENTALS*
[2-3 bullet points on key fundamental metrics]

📉 *TECHNICAL ANALYSIS*
[2-3 bullet points on key technical signals]

⚡ *SHORT-TERM (1-3 months)*
Outlook: [BULLISH/BEARISH/NEUTRAL]
[1-2 sentences]

🚀 *LONG-TERM (1-3 years)*
Outlook: [BULLISH/BEARISH/NEUTRAL]
[1-2 sentences]

🎯 *VERDICT: [BUY / HOLD / SELL / AVOID]*
[1-2 sentences explaining the verdict and risk level]

⚠️ *Risk Level: [LOW/MEDIUM/HIGH]*

Keep it concise and WhatsApp-friendly. Be direct with your recommendation. Always mention the most important risk factor."""


def _build_analysis_prompt(stock_data: dict, asset_type: str) -> str:
    price = stock_data.get("price", {})
    fund = stock_data.get("fundamentals", {})
    tech = stock_data.get("technical", {})
    vol = stock_data.get("volume", {})

    lines = [
        f"Asset Type: {asset_type.upper()}",
        f"Ticker: {stock_data.get('ticker')}",
        f"Name: {stock_data.get('name')}",
        f"Sector: {stock_data.get('sector')}",
        f"Industry: {stock_data.get('industry')}",
        "",
        "=== PRICE DATA ===",
        f"Current Price: {price.get('current')} {stock_data.get('currency', 'USD')}",
        f"Day Change: {price.get('change')} ({price.get('change_pct')}%)",
        f"52-Week High: {price.get('week_52_high')}",
        f"52-Week Low: {price.get('week_52_low')}",
        f"52-Week Position: {price.get('week_52_position_pct')}% (100=at high, 0=at low)",
        f"1-Month Return: {price.get('return_1m_pct')}%",
        f"3-Month Return: {price.get('return_3m_pct')}%",
        f"6-Month Return: {price.get('return_6m_pct')}%",
        f"YTD Return: {price.get('return_ytd_pct')}%",
        "",
    ]

    if asset_type == "stock":
        lines += [
            "=== FUNDAMENTALS ===",
            f"Market Cap: {fund.get('market_cap')}",
            f"P/E (TTM): {fund.get('pe_ratio')}",
            f"Forward P/E: {fund.get('forward_pe')}",
            f"P/B Ratio: {fund.get('pb_ratio')}",
            f"P/S Ratio: {fund.get('ps_ratio')}",
            f"EV/EBITDA: {fund.get('ev_ebitda')}",
            f"PEG Ratio: {fund.get('peg_ratio')}",
            f"EPS (TTM): {fund.get('eps_ttm')}",
            f"Forward EPS: {fund.get('eps_forward')}",
            f"Profit Margin: {fund.get('profit_margin')}",
            f"Operating Margin: {fund.get('operating_margin')}",
            f"ROE: {fund.get('roe')}",
            f"ROA: {fund.get('roa')}",
            f"Revenue (TTM): {fund.get('revenue_ttm')}",
            f"Revenue Growth YoY: {fund.get('revenue_growth_yoy')}",
            f"Earnings Growth YoY: {fund.get('earnings_growth_yoy')}",
            f"Debt/Equity: {fund.get('debt_to_equity')}",
            f"Current Ratio: {fund.get('current_ratio')}",
            f"Free Cash Flow: {fund.get('free_cash_flow')}",
            f"Dividend Yield: {fund.get('dividend_yield')}",
            f"Beta: {fund.get('beta')}",
            f"Analyst Target Price: {fund.get('analyst_target')}",
            f"Analyst Recommendation: {fund.get('analyst_recommendation')}",
            f"Number of Analysts: {fund.get('analyst_count')}",
            "",
        ]

    lines += [
        "=== TECHNICAL INDICATORS ===",
        f"Overall Trend: {tech.get('trend')}",
        f"RSI (14): {tech.get('rsi')} (>70=overbought, <30=oversold)",
        f"MA20: {tech.get('ma20')} | Above MA20: {tech.get('above_ma20')}",
        f"MA50: {tech.get('ma50')} | Above MA50: {tech.get('above_ma50')}",
        f"MA200: {tech.get('ma200')} | Above MA200: {tech.get('above_ma200')}",
        f"Golden Cross (MA50>MA200): {tech.get('golden_cross')}",
        f"MACD: {tech.get('macd')} | Signal: {tech.get('macd_signal')}",
        f"MACD Bullish: {tech.get('macd_bullish')} | Momentum: {tech.get('macd_momentum')}",
        f"Bollinger Band %B: {tech.get('bb_pct_b')} (>1=above upper, <0=below lower)",
        f"BB Bandwidth: {tech.get('bb_bandwidth')}% | Squeeze: {tech.get('bb_squeeze')}",
        f"ATR (14): {tech.get('atr_14')}",
        f"Pivot: {tech.get('pivot')} | R1: {tech.get('resistance_1')} | S1: {tech.get('support_1')}",
        f"Volume Trend: {tech.get('volume_trend')}",
        f"Volume Ratio (vs 30d avg): {vol.get('ratio')}x",
    ]

    return "\n".join(str(line) for line in lines)
