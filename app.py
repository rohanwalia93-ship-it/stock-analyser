import os
from flask import Flask, request, Response
from dotenv import load_dotenv
from twilio.request_validator import RequestValidator

from whatsapp import handle_message, send_whatsapp_message

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
