import os
import requests
from dotenv import load_dotenv

# Force load the .env file
load_dotenv()

# Fetch from environment
TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("PHONE_NUMBER_ID")

# DEBUG: Check if it loaded (Remove this line after testing)
if not TOKEN:
    print("❌ ERROR: .env file not found or WHATSAPP_TOKEN is missing!")
else:
    print(f"✅ Token Loaded successfully (Starts with {TOKEN[:5]}...)")

def send_whatsapp_message(to_number, text_body):
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text_body}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"✅ Reply sent to {to_number}!")
    else:
        print(f"❌ Failed to send: {response.text}")