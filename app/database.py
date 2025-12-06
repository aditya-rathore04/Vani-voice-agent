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
    
    threshold = 70
    
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

    # --- NEW LOGIC: CHECK FOR LEAVE ---
    # We loop through results to flag if they are on leave
    for row in rows:
        availability = row.get("availability", "").upper()
        if "LEAVE" in availability or "ABSENT" in availability or "UNAVAILABLE" in availability:
            # We explicitly mark this in the data returned to the LLM
            row["status"] = "ON_LEAVE" 
            row["note"] = "This doctor is currently NOT available."
        else:
            row["status"] = "AVAILABLE"

    return {"type": "specific_result", "data": rows}