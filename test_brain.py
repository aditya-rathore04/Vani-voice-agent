# test_brain.py
from dotenv import load_dotenv
import os

load_dotenv()
KEY = os.getenv("GROQ_API_KEY")

print(f"🔑 Checking Key: {KEY[:5] if KEY else 'None'}")

try:
    from app.ai_engine import chat_with_llama
    print("✅ Import successful!")
    
    response = chat_with_llama("Is Dr. Sharma available?")
    print(f"🤖 AI Replied: {response}")
    
except Exception as e:
    print(f"❌ CRASHED: {e}")
    import traceback
    traceback.print_exc()