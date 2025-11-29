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

def chat_with_llama(user_text, history=[]):
    # 1. Get Current Time
    current_time = datetime.now().strftime("%A, %I:%M %p") # e.g., "Saturday, 06:30 PM"
    
    # 2. Dynamic System Prompt
    system_prompt_text = f"""
    You are Vani, a helpful receptionist at City Health Clinic.
    Current Time: {current_time}
    
    GOAL: Answer patient queries about doctor availability.

    RULES:
    1. CHECK HISTORY FIRST: If the user asks a follow-up (e.g., "Is she there?", "What about now?"), use the data you ALREADY found in the previous turn. DO NOT call a tool again unless necessary.
    2. Enforce "Enquiry Only": You cannot book appointments.
    3. Keep answers concise and natural. Don't repeat the full schedule if the user just wants a "Yes/No".

    TOOLS:
    - Search Doctor/Specialty: Output JSON {{"tool": "check_doctor", "name": "keyword"}}
    - Check ALL availability: Output JSON {{"tool": "check_doctor", "name": "all"}}
    - Output ONLY JSON if using a tool.
    """

    # 3. Add System Prompt to Messages
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