import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Отправь /start боту @ScheduleSurguBot в Telegram
print("📱 Отправь /start боту в Telegram, затем нажми Enter...")
input()

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
response = requests.get(url)
data = response.json()

if data.get("result"):
    for update in data["result"]:
        chat = update.get("message", {}).get("chat", {})
        chat_id = chat.get("id")
        first_name = chat.get("first_name", "")
        username = chat.get("username", "")

        print(f"\n✅ ТВОЙ CHAT ID: {chat_id}")
        print(f"   Имя: {first_name}")
        print(f"   Username: @{username}")
        print(f"\n👉 Используй это число: {chat_id}")
else:
    print("❌ Обновлений нет. Отправь /start боту и попробуй снова.")
