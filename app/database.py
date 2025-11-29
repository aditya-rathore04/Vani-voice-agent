# app/database.py
import sqlite3
from thefuzz import process

DB_PATH = "data/clinic.db"

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
    # If the user asks "Who is available at 2pm?", the LLM might query "all" or "available"
    if query_str.lower() in ["all", "anyone", "available", "doctor", "doctors"]:
        cursor.execute("SELECT * FROM schedule")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"type": "full_schedule", "data": results}

    # 3. Fuzzy Search Logic
    # Check if input matches a Doctor Name
    best_doc, doc_score = process.extractOne(query_str, doctor_names) if doctor_names else (None, 0)
    
    # Check if input matches a Department (Specialty)
    best_dept, dept_score = process.extractOne(query_str, departments) if departments else (None, 0)
    
    # 4. Decide Winner
    threshold = 70
    
    # Case A: It's a Department (e.g., "Cardiologist" -> "Cardiology")
    if dept_score > threshold and dept_score > doc_score:
        print(f"🔍 Searching by Department: {best_dept} (Score: {dept_score})")
        cursor.execute("SELECT * FROM schedule WHERE department = ?", (best_dept,))
        
    # Case B: It's a Doctor Name (e.g., "Sharma" -> "Dr. Sharma")
    elif doc_score > threshold:
        print(f"🔍 Searching by Name: {best_doc} (Score: {doc_score})")
        cursor.execute("SELECT * FROM schedule WHERE doctor_name = ?", (best_doc,))
        
    if not (dept_score > threshold or doc_score > threshold):
        # Fetch valid departments to help the user
        conn.row_factory = None # Reset to normal list
        cursor.execute("SELECT DISTINCT department FROM schedule")
        valid_depts = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Return a "Helpful Error" object
        return {
            "error": "not_found", 
            "valid_departments": valid_depts
        }

    # Fetch results
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"type": "specific_result", "data": rows}