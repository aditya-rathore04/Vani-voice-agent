# app/ai_engine.py
import os
import json
import re
from datetime import datetime  # <--- NEW IMPORT
from groq import Groq
from dotenv import load_dotenv
from app.database import get_doctor_info  # The tool we made in Part A

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def chat_with_llama(user_text, language_code, history=[]):
    current_time = datetime.now().strftime("%A, %I:%M %p")
    
    # 📝 UPDATED PROMPT: Universal Translation Rules
    system_prompt_text = f"""
    You are Vani, a receptionist at City Health Clinic.
    Current Time: {current_time}
    User's Language Code: {language_code} 

    GOAL: Answer in the user's language, but Query the database in English.

    RULES:
    1. RESPONSE LANGUAGE: You MUST reply in the user's language ('{language_code}').
       - 'en' -> English, 'hi' -> Hindi, 'kn' -> Kannada, 'ml' -> Malayalam.
    
    2. TOOL ARGUMENTS (CRITICAL): 
       - The database is 100% ENGLISH.
       - NEVER output Hindi/Kannada/Malayalam script inside the JSON.
       - TRANSLATE patient terms to medical English terms.
       
       EXAMPLES:
       - User (Hindi): "अंजली" -> Tool: {{"tool": "check_doctor", "name": "Anjali"}}
       - User (Malayalam): "ഹൃദ്രോഗ വിദഗ്ധൻ" (Heart Doctor) -> Tool: {{"tool": "check_doctor", "name": "Cardiologist"}}
       - User (Kannada): "ಚರ್ಮ ವೈದ್ಯ" (Skin Doctor) -> Tool: {{"tool": "check_doctor", "name": "Dermatologist"}}
       - User (English): "Eye specialist" -> Tool: {{"tool": "check_doctor", "name": "Ophthalmologist"}}

    3. HISTORY: Check history first. Don't call tools if you already have the answer.

    4. Enforce "Enquiry Only": No bookings.

    TOOLS:
    - Search: {{"tool": "check_doctor", "name": "english_keyword"}}
    - Output ONLY JSON if using a tool.
    """

    messages = [{"role": "system", "content": system_prompt_text}] + history + [{"role": "user", "content": user_text}]
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
            
            if "error" in db_result and db_result["error"] == "not_found":
                # The DB search failed. We give this info to Llama.
                valid_list = ", ".join(db_result["valid_departments"])
                
                tool_msg = f"TOOL RESULT: No doctor or specialty found matching '{doctor_name}'. Available Departments are: {valid_list}. Inform the user politely."
                
                final_messages = messages + [
                    {"role": "assistant", "content": ai_reply},
                    {"role": "user", "content": tool_msg}
                ]
                
            else:
                # Success! We found data.
                final_messages = messages + [
                    {"role": "assistant", "content": ai_reply},
                    {"role": "user", "content": f"TOOL RESULT: {json.dumps(db_result)}"}
                ]
            
            # Generate the final answer (Success OR Failure)
            final_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=final_messages
            )
            return final_response.choices[0].message.content
        except Exception as e:
            print(f"❌ JSON Parsing Error: {e}")
            return "I'm having trouble checking the schedule right now."

    # If no tool needed, just return the text (e.g., "Hello!")
    return ai_reply