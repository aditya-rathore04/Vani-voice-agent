# app/ai_engine.py
import os
import json
from groq import Groq
from dotenv import load_dotenv
from app.database import get_doctor_info  # The tool we made in Part A

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 1. The Persona (System Prompt)
# We tell Llama 3 exactly how to behave and how to use tools.
SYSTEM_PROMPT = """
You are Vani, a helpful receptionist at City Health Clinic.
Your goal is to answer patient queries about doctor availability.

TOOLS AVAILABLE:
- You can check doctor schedules.

INSTRUCTIONS:
1. If the user asks for a doctor (e.g., "Is Dr. Sharma in?", "Cardiologist available?"), 
   you MUST output a JSON object: {"tool": "check_doctor", "name": "extracted_name"}
   
2. If the user asks a general question (e.g., "Hi", "Where are you?"), 
   just reply normally as text. Do NOT output JSON.

3. If you get DATA back from a tool, summarize it nicely for the user in their language.
"""

def chat_with_llama(user_text):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]

    # Call 1: Ask Llama what to do (Think)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3  # Low temperature = more precise tool calling
    )
    
    ai_reply = response.choices[0].message.content

    # Check if Llama wants to use a tool (JSON detection)
    if "{" in ai_reply and "check_doctor" in ai_reply:
        try:
            # Parse the JSON signal
            tool_data = json.loads(ai_reply)
            doctor_name = tool_data["name"]
            
            # Run the Python Tool (The Hands)
            print(f"🛠️ AI is calling tool for: {doctor_name}")
            db_result = get_doctor_info(doctor_name)
            
            if db_result:
                # Feed data back to Llama for the final answer
                final_messages = messages + [
                    {"role": "assistant", "content": ai_reply},
                    {"role": "system", "content": f"TOOL RESULT: {json.dumps(db_result)}. Now answer the user."}
                ]
                final_response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=final_messages
                )
                return final_response.choices[0].message.content
            else:
                return f"Sorry, I couldn't find a doctor named {doctor_name} in our system."

        except Exception as e:
            print(f"❌ JSON Parsing Error: {e}")
            return "I'm having trouble checking the schedule right now."

    # If no tool needed, just return the text (e.g., "Hello!")
    return ai_reply