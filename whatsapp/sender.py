import os
from twilio.rest import Client

MAX_WHATSAPP_LENGTH = 1600


def send_whatsapp_message(to: str, body: str) -> None:
    """Send a WhatsApp message via Twilio. Splits long messages automatically."""
    client = Client(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"],
    )
    from_number = os.environ["TWILIO_WHATSAPP_NUMBER"]

    for chunk in _split_message(body):
        client.messages.create(
            from_=from_number,
            to=to,
            body=chunk,
        )


def _split_message(text: str, limit: int = MAX_WHATSAPP_LENGTH) -> list[str]:
    if len(text) <= limit:
        return [text]

    parts = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        parts.append(text[:split_at].rstrip())
        text = text[split_at:].lstrip()
    if text:
        parts.append(text)
    return parts
