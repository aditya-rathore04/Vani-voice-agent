# app/ai_engine.py
import os
import json
import re
from datetime import datetime  # <--- NEW IMPORT
from groq import Groq
from dotenv import load_dotenv
from app.database import get_doctor_info  # The tool we made in Part A
from app.database import get_doctor_info, get_clinic_overview  # <--- Import new function

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def chat_with_llama(user_text, language_code, history=[]):
    # 1. PREPARE PROMPT DATA
    # Result: "Friday, 06 December 2025, 07:30 PM" (Includes Date for future checks)
    current_time = datetime.now().strftime("%A, %d %B %Y, %I:%M %p") 
    clinic_knowledge = get_clinic_overview()
    
    # 2. SYSTEM PROMPT (Your detailed, fixed prompt structure)
    system_prompt_text = f"""
    You are Vani, a receptionist at City Health Clinic.
    Current Time: {current_time}
    User's Language Code: {language_code} 

    CLINIC OVERVIEW (What we have):
    {clinic_knowledge}
    (NOTE: If a user asks for a specialist NOT in this list, say we don't have them. Do not ask if they want to see 'others' if only one exists.)

    GOAL: Answer in the user's language, but Query the database in English.

    RULES:
    1. RESPONSE LANGUAGE: You MUST reply in the user's language ('{language_code}').
        - 'en' -> English, 'hi' -> Hindi, 'kn' -> Kannada, 'ml' -> Malayalam.

    2. TIME CHECK (CRITICAL):
        - ALWAYS compare the 'Current Time' with the doctor's schedule.
        - If the doctor's hours are over (e.g., Schedule: 8am-8pm, Current Time: 8:43pm), say they are NOT available now but mention when they will be available next (e.g., "tomorrow at 8am").
        - Be precise. 8:43 PM is AFTER 8:00 PM.

    3. WALK-IN CLINIC LOGIC (CRITICAL):
        - This is a WALK-IN clinic. We do not have "slots" or "bookings".
        - If the schedule says a doctor is here (e.g., "Daily 8am-8pm"), then they ARE available.
        - DO NOT say "Let me check availability" if you already see the schedule. Just say "Yes, come in."
        - If the user asks for a specific time (e.g., "Tomorrow evening?"), compare it with the schedule. If it fits, say YES. Do not ask to check again.
    
    4. TOOL ARGUMENTS (CRITICAL): 
        - The database is 100% ENGLISH.
        - NEVER output Hindi/Kannada/Malayalam script inside the JSON.
        - TRANSLATE patient terms to medical English terms.
            EXAMPLES:
            - User (Symptom): "I feel feverish" -> Tool: {{"tool": "check_doctor", "name": "General"}} 
            - User (Hindi): "अंजली" -> Tool: {{"tool": "check_doctor", "name": "Anjali"}}
            - User (Malayalam): "ഹൃദ്രോഗ വിദഗ്ധൻ" (Heart Doctor) -> Tool: {{"tool": "check_doctor", "name": "Cardiologist"}}
            - "All doctors / Schedule" -> Tool: {{"tool": "check_doctor", "name": "all"}}
        - PHONETIC CORRECTION: If the user says a name that SOUNDS like a doctor in the "CLINIC OVERVIEW", use the correct doctor's name.
          - "Swarma" / "Sarma" -> {{"tool": "check_doctor", "name": "Sharma"}}
          - "Gupta ji" -> {{"tool": "check_doctor", "name": "Gupta"}}
          - "Anjili" -> {{"tool": "check_doctor", "name": "Anjali"}}

    5. AUDIO FORMAT (CRITICAL):
       - You are speaking on a VOICE CALL. Do not use visual formatting.
       - NO Newlines (\n). NO Bullet points. NO Lists.
       - NO bold (**text**) or markdown.
       - Speak in one continuous, flowing paragraph.
       - Use commas and periods for pauses.
       - Bad: "We have:\n- Dr. A\n- Dr. B"
       - Good: "We have Dr. A and Dr. B available."   

    6. HISTORY: Check history first. 
        - If the user says "Yes" to a suggestion (e.g., "Want to see General doctor?"), CALL THE TOOL for that specific department ("General").
        - If the user changes topic completely, call the tool.

    7. Enforce "Enquiry Only": No bookings.

    8. STOPPING RULE (CRITICAL): 
        - If the user says "No", "Thanks", "Bye", "Okay", or "That's all", DO NOT CALL ANY TOOLS.
        - Just say a polite goodbye or "You're welcome".

    TOOLS:
    - Search: {{"tool": "check_doctor", "name": "english_keyword"}}
    - Output ONLY JSON if using a tool.
    """

    messages = [{"role": "system", "content": system_prompt_text}] + history + [{"role": "user", "content": user_text}]
    
    # 3. CALL LLAMA (Lower temperature for precision)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.1  # <-- Lowered for reliable JSON/Tool output
    )
    
    ai_reply = response.choices[0].message.content
    
    # 4. ROBUST JSON DETECTION (The fix for the crash)
    # This regex searches the whole string for the first JSON object { ... }
    json_match = re.search(r"\{[\s\S]*?\}", ai_reply) 
    
    # Check if a JSON object was found AND if it contains the tool name
    if json_match and "check_doctor" in ai_reply:
        try:
            # Extract the raw JSON string
            json_str = json_match.group() 
            tool_data = json.loads(json_str)
            doctor_name = tool_data["name"]
            
            # Run the Python Tool (The Hands)
            print(f"🛠️ AI is calling tool for: {doctor_name}")
            db_result = get_doctor_info(doctor_name)
            
            # ... (Rest of your existing tool result handling logic is fine) ...
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
            # This handles both JSONDecodeError and any error in the tool logic
            print(f"❌ JSON Parsing/Tool Error: {e}")
            return "I'm having trouble checking the schedule right now."

    # 5. NO TOOL NEEDED (e.g., "Hi", "No thanks")
    return ai_reply