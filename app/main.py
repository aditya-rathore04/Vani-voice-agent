# app/main.py (Updated with Memory)
from fastapi import FastAPI, Request, Query
import uvicorn
import os
from dotenv import load_dotenv
from app.whatsapp_client import send_whatsapp_message
from app.ai_engine import chat_with_llama

load_dotenv()
app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN") or "vani_secret_123"

# 🧠 MEMORY STORAGE
# Structure: { "91999...": [ {"role": "user", "content": "..."}, ... ] }
CHAT_HISTORY = {} 

@app.get("/webhook")
async def verify_webhook(mode: str = Query(alias="hub.mode"), token: str = Query(alias="hub.verify_token"), challenge: str = Query(alias="hub.challenge")):
    if mode == "subscribe" and token == VERIFY_TOKEN: return int(challenge)
    return {"error": "Invalid token"}, 403

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        
        if "messages" in value:
            message_data = value["messages"][0]
            sender_id = message_data["from"]
            
            if message_data["type"] == "text":
                user_text = message_data["text"]["body"]
                print(f"🗣️ User ({sender_id}) said: {user_text}")

                # 1. GET HISTORY
                # Fetch previous messages for this user (default to empty list)
                user_history = CHAT_HISTORY.get(sender_id, [])

                # 2. CALL BRAIN (Pass history!)
                ai_response = chat_with_llama(user_text, user_history)
                print(f"🤖 Vani says: {ai_response}")

                # 3. UPDATE HISTORY (Save this turn)
                # Append User Message
                user_history.append({"role": "user", "content": user_text})
                # Append AI Reply
                user_history.append({"role": "assistant", "content": ai_response})
                
                # Keep only last 10 messages to save RAM
                CHAT_HISTORY[sender_id] = user_history[-10:]

                # 4. SEND REPLY
                send_whatsapp_message(sender_id, ai_response)
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        pass

    return {"status": "received"}