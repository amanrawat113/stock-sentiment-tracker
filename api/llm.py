import os
import requests
from dotenv import load_dotenv
load_dotenv()

OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")
OLLAMA_CHAT_URL = "https://ollama.com/api/chat"


def generate_market_summary(alerts: list) -> str:
    if not alerts:
        return "No significant market signals detected today."

    alert_lines = []
    for a in alerts:
        alert_lines.append(
            f"- {a['company_name']} ({a['symbol']}): net sentiment {a['net_sentiment']}, "
            f"{a['total_announcements']} announcements"
        )
    alerts_text = "\n".join(alert_lines)

    prompt = (
        "You are a financial market analyst. Based on the following stock sentiment "
        "signals, write a short (3-5 sentence) natural-language market brief for a retail "
        "investor. Be factual and concise, no speculation beyond what's given.\n\n"
        f"{alerts_text}"
    )

    response = requests.post(
        OLLAMA_CHAT_URL,
        headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"},
        json={
            "model": "gpt-oss:20b",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]