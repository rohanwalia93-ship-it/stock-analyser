import os
from flask import Flask, request, Response, render_template, jsonify
from dotenv import load_dotenv
from twilio.request_validator import RequestValidator

from whatsapp import handle_message, send_whatsapp_message
from analyzer import fetch_stock_data, resolve_ticker, analyze_stock

load_dotenv()

app = Flask(__name__)


@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_webhook():
    # Validate the request is genuinely from Twilio
    if not _validate_twilio_request():
        return Response("Forbidden", status=403)

    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From", "")

    if not sender:
        return Response("Bad Request", status=400)

    reply = handle_message(incoming_msg)
    send_whatsapp_message(sender, reply)

    return Response("", status=204)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/analyse", methods=["POST"])
def api_analyse():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()

    if not query:
        return jsonify({"error": "Please enter a stock, commodity, or crypto name."}), 400

    ticker, asset_type = resolve_ticker(query)
    stock_data = fetch_stock_data(ticker)

    if stock_data is None or "error" in stock_data:
        return jsonify({"error": f"Could not find data for \"{query}\". Try a ticker symbol like AAPL or TSLA."}), 404

    result = analyze_stock(stock_data, asset_type)
    return jsonify({"result": result, "ticker": ticker, "asset_type": asset_type})


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


def _validate_twilio_request() -> bool:
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    if not auth_token:
        return False

    validator = RequestValidator(auth_token)
    url = request.url
    params = request.form.to_dict()
    signature = request.headers.get("X-Twilio-Signature", "")

    return validator.validate(url, params, signature)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
