# app/admin_ai.py
import os
import json
import re
from datetime import datetime # <--- NEW IMPORT
from groq import Groq
from dotenv import load_dotenv
from app.database import update_doctor_schedule

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def process_admin_command(user_text):
    # Get current day for "Today/Tomorrow" logic
    today = datetime.now().strftime("%A") 
    
    ADMIN_PROMPT = f"""
    You are the Database Admin AI. Current Day: {today}.
    Extract commands to update the doctor schedule.

    TOOLS:
    - Update Status: {{"tool": "update_schedule", "name": "Dr. Name", "day": "Day", "status": "New Status"}}

    RULES:
    1. If the admin mentions a specific day (e.g., "Monday"), include it in "day".
    2. If the admin says "Today", calculate the day from {today}.
    3. If NO day is mentioned, output "ALL" in the "day" field (updates all days).

    EXAMPLES:
    - "Mark Dr. Sharma absent on Monday" -> {{"tool": "update_schedule", "name": "Sharma", "day": "Monday", "status": "ON LEAVE"}}
    - "Cancel Dr. Gupta today" -> {{"tool": "update_schedule", "name": "Gupta", "day": "{today}", "status": "Emergency Leave"}}
    - "Dr. Anjali is available" -> {{"tool": "update_schedule", "name": "Anjali", "day": "ALL", "status": "Available"}}
    """

    messages = [{"role": "system", "content": ADMIN_PROMPT}, {"role": "user", "content": user_text}]
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.1
        )
        ai_reply = response.choices[0].message.content
        
        json_match = re.search(r"\{[\s\S]*?\}", ai_reply)
        if json_match:
            tool_data = json.loads(json_match.group())
            if tool_data.get("tool") == "update_schedule":
                # PASS THE DAY TO THE DATABASE FUNCTION
                result = update_doctor_schedule(
                    tool_data["name"], 
                    tool_data["status"], 
                    tool_data.get("day", "ALL") # Default to ALL if missing
                )
                return result["message"]
        
        return ai_reply

    except Exception as e:
        return f"Error: {str(e)}"