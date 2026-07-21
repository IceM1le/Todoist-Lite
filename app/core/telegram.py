import httpx
from app.core.config import settings

TELEGRAM_TOKEN = settings.TELEGRAM_TOKEN

def send_telegram_message(text: str, chat_id: str) -> bool:
    """Отправляет сообщение в Telegram """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        with httpx.Client() as client:
            response = client.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False