from analyzer import fetch_stock_data, resolve_ticker, analyze_stock

HELP_TEXT = """👋 *Stock Analyser Bot*

Send me any stock, commodity, or crypto name and I'll analyse it for you!

*Examples:*
• Tesla
• Gold
• Bitcoin
• NVDA
• S&P 500

I'll send back fundamentals, technical analysis, and a clear BUY/SELL recommendation."""

UNKNOWN_TEXT = """❓ I couldn't find data for *{query}*.

Try using a ticker symbol (e.g. AAPL, TSLA) or a common name (e.g. Tesla, Gold, Bitcoin)."""

ERROR_TEXT = """⚠️ Something went wrong while analysing *{query}*. Please try again in a moment."""


def handle_message(body: str) -> str:
    """Process an incoming WhatsApp message body and return the reply text."""
    text = body.strip()

    if not text or text.lower() in ("hi", "hello", "hey", "help", "start", "/start", "/help"):
        return HELP_TEXT

    ticker, asset_type = resolve_ticker(text)

    stock_data = fetch_stock_data(ticker)

    if stock_data is None:
        return UNKNOWN_TEXT.format(query=text)

    if "error" in stock_data:
        return UNKNOWN_TEXT.format(query=text)

    try:
        analysis = analyze_stock(stock_data, asset_type)
        return analysis
    except Exception:
        return ERROR_TEXT.format(query=text)
