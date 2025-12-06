# app/main.py (Updated with Memory)
from app.audio import transcribe_audio, generate_voice_note
from app.whatsapp_client import get_media_url, download_media_file, upload_media, send_whatsapp_audio, send_whatsapp_message
from fastapi import FastAPI, Request, Query
import uvicorn
import os
from dotenv import load_dotenv
from app.whatsapp_client import send_whatsapp_message
from app.ai_engine import chat_with_llama
from app.admin_ai import process_admin_command  # <--- NEW IMPORT

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
            
            ADMIN_NUMBER = os.getenv("ADMIN_PHONE") # Add your number to .env!

            # 👑 GOD MODE CHECK
            if sender_id == ADMIN_NUMBER:
                print(f"👑 ADMIN COMMAND from {sender_id}")
                
                # Extract text from either Text or Audio message
                command_text = ""
                if message_data["type"] == "text":
                    command_text = message_data["text"]["body"]
                elif message_data["type"] == "audio":
                    audio_id = message_data["audio"]["id"]
                    media_url = get_media_url(audio_id)
                    ogg_path = f"data/{sender_id}_admin.ogg"
                    download_media_file(media_url, ogg_path)
                    command_text, _ = transcribe_audio(ogg_path) # Ignore lang for admin
                
                # Process Command
                if command_text:
                    print(f"🔧 Command: {command_text}")
                    response_text = process_admin_command(command_text)
                    # Send Text Reply back to Admin (Faster/Easier)
                    send_whatsapp_message(sender_id, f"✅ {response_text}")
                
                return {"status": "processed_as_admin"}

            if message_data["type"] == "text":
                user_text = message_data["text"]["body"]
                print(f"🗣️ User ({sender_id}) said: {user_text}")

                # 1. GET HISTORY
                # Fetch previous messages for this user (default to empty list)
                user_history = CHAT_HISTORY.get(sender_id, [])

                
                # Default to English for text, or you can try to detect it if you want.
                # For now, "en" is safe because most text inputs on WhatsApp are English/Hinglish.
                detected_lang = "en" 

                # 2. CALL BRAIN (Pass language!)
                ai_response = chat_with_llama(user_text, detected_lang, user_history)
                
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
                
            elif message_data["type"] == "audio":
                audio_id = message_data["audio"]["id"]
                
                # 1. Download
                media_url = get_media_url(audio_id)
                ogg_path = f"data/{sender_id}_input.ogg"
                download_media_file(media_url, ogg_path)
                
                # 2. Transcribe (Ears) - NOW RETURNS LANGUAGE
                print("👂 Transcribing...")
                user_text, detected_lang = transcribe_audio(ogg_path) # <--- Get Lang
                print(f"🗣️ Transcribed ({detected_lang}): {user_text}")
                
                # 3. Brain (LLM) - PASS LANGUAGE
                user_history = CHAT_HISTORY.get(sender_id, [])
                ai_response = chat_with_llama(user_text, detected_lang, user_history) # <--- Pass Lang
                print(f"🤖 AI Reply: {ai_response}")
                
                # Update Memory
                user_history.append({"role": "user", "content": user_text})
                user_history.append({"role": "assistant", "content": ai_response})
                CHAT_HISTORY[sender_id] = user_history[-10:]
                
                # 4. Speak (Mouth) - PASS LANGUAGE
                print(f"👄 Generating Voice Note ({detected_lang})...")
                output_ogg = f"data/{sender_id}_reply.ogg"
                
                # Edge-TTS will now pick the matching Kannada/Malayalam voice
                await generate_voice_note(ai_response, detected_lang, output_ogg) 
                
                # 5. Delivery
                media_id = upload_media(output_ogg)
                send_whatsapp_audio(sender_id, media_id)
                
                # Cleanup
                if os.path.exists(ogg_path): os.remove(ogg_path)
                if os.path.exists(output_ogg): os.remove(output_ogg)

    except Exception as e:
        print(f"❌ ERROR: {e}")
        pass

    return {"status": "received"}