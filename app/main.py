# app/main.py
from fastapi import FastAPI, Request, Query
import uvicorn
import os
from dotenv import load_dotenv
from app.whatsapp_client import send_whatsapp_message
from app.ai_engine import chat_with_llama

# Force load .env
load_dotenv()

app = FastAPI()

# Fetch from environment
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# DEBUG CHECK
if not VERIFY_TOKEN:
    print("⚠️ WARNING: VERIFY_TOKEN not found in .env!")

@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return {"error": "Invalid token"}, 403

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    
    try:
        # 1. Dig into the JSON to find the message
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        
        # Check if there is a message (sometimes it's just a status update)
        if "messages" in value:
            message_data = value["messages"][0]
            sender_id = message_data["from"] # The user's phone number
            
            # 2. Check if it is TEXT
            if message_data["type"] == "text":
                user_text = message_data["text"]["body"]
                print(f"🗣️ User said: {user_text}")
                
                # 3. LOGIC: The Echo Bot
                # (Replaced the old echo code with this)
                ai_response = chat_with_llama(user_text)
                
                print(f"🤖 Vani says: {ai_response}")

                # 4. SEND REPLY
                send_whatsapp_message(sender_id, ai_response)
                
    except Exception as e:
        # If the JSON structure is different (status update), ignore it
        pass

    return {"status": "received"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)