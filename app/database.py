# app/database.py
import sqlite3
from thefuzz import process

DB_PATH = "data/clinic.db"

def get_clinic_overview():
    """
    Returns a summary string of all departments and doctors.
    Used for the System Prompt so the LLM knows what we have.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT doctor_name, department FROM schedule GROUP BY doctor_name")
    rows = cursor.fetchall()
    conn.close()
    
    # Create a summary like: "- Cardiology (Dr. Sharma)\n- General (Dr. Anjali)"
    overview = []
    for name, dept in rows:
        overview.append(f"- {dept}: {name}")
    
    return "\n".join(overview)

def get_doctor_info(query_str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    cursor = conn.cursor()
    
    # 1. Fetch Lists for Fuzzy Matching
    cursor.execute("SELECT DISTINCT doctor_name FROM schedule")
    doctor_names = [row['doctor_name'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT department FROM schedule")
    departments = [row['department'] for row in cursor.fetchall()]
    
    # 2. Logic: "All Doctors" request
    q = query_str.lower()
    if "all" in q or "schedule" in q or "doctors" in q or "anyone" in q:
        print("🔍 Searching for ALL doctors")
        cursor.execute("SELECT * FROM schedule")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"type": "full_schedule", "data": results}

    # 3. Fuzzy Search Logic
    best_doc, doc_score = process.extractOne(query_str, doctor_names) if doctor_names else (None, 0)
    best_dept, dept_score = process.extractOne(query_str, departments) if departments else (None, 0)
    
    threshold = 60  # Minimum score to consider a match
    
    # Case A: Department Match
    if dept_score > threshold and dept_score > doc_score:
        print(f"🔍 Searching by Department: {best_dept} (Score: {dept_score})")
        cursor.execute("SELECT * FROM schedule WHERE department = ?", (best_dept,))
        
    # Case B: Doctor Name Match
    elif doc_score > threshold:
        print(f"🔍 Searching by Name: {best_doc} (Score: {doc_score})")
        cursor.execute("SELECT * FROM schedule WHERE doctor_name = ?", (best_doc,))
        
    # Case C: No match found
    else:
        conn.row_factory = None
        cursor.execute("SELECT DISTINCT department FROM schedule")
        valid_depts = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {
            "error": "not_found", 
            "valid_departments": valid_depts
        }

    # Fetch results
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

   # --- UPDATED LOGIC: COMBINE TIME & STATUS ---
    final_data = []
    
    for row in rows:
        # Get raw values
        time_slot = row.get("schedule_time", "Unknown")
        status = row.get("current_status", "Available")
        
        # Logic to decide what the LLM sees
        if status.upper() != "AVAILABLE":
            # If on leave, override the message to be very clear
            availability_msg = f"Currently {status} (Standard Time: {time_slot})"
            is_active = False
        else:
            # If available, just show the time
            availability_msg = time_slot
            is_active = True
            
        final_data.append({
            "doctor": row["doctor_name"],
            "day": row["day"],
            "status": status,           # Explicit Status field
            "availability": availability_msg, # Combined human-readable string
            "is_active": is_active      # Boolean flag for ease
        })

    return {"type": "specific_result", "data": final_data}

def update_doctor_schedule(doctor_name, new_status, day="ALL"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Fuzzy Match Doctor Name
    cursor.execute("SELECT DISTINCT doctor_name FROM schedule")
    all_doctors = [row[0] for row in cursor.fetchall()]
    best_match, score = process.extractOne(doctor_name, all_doctors)
    
    if score < 80:
        conn.close()
        return {"status": "error", "message": f"Could not find doctor '{doctor_name}'."}
    
    # 2. Update Logic
    if day.upper() == "ALL":
        # Update ALL days for this doctor
        cursor.execute("UPDATE schedule SET current_status = ? WHERE doctor_name = ?", (new_status, best_match))
        msg = f"Updated {best_match} (All Days) to: {new_status}"
    else:
        # Update ONLY the specific day
        # We use fuzzy matching for days too, to handle "Mon" vs "Monday"
        valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Daily"]
        best_day, day_score = process.extractOne(day, valid_days)
        
        cursor.execute("UPDATE schedule SET current_status = ? WHERE doctor_name = ? AND day = ?", (new_status, best_match, best_day))
        msg = f"Updated {best_match} ({best_day}) to: {new_status}"

    conn.commit()
    conn.close()
    
    return {"status": "success", "message": msg}