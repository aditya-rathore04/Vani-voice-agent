# app/database.py
import sqlite3
from thefuzz import process

DB_PATH = "data/clinic.db"

def get_doctor_info(query_name):
    """
    Searches for a doctor by name using fuzzy matching.
    Handles: 'Sarma', 'Gupta ji', 'Dr Anjli'
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Get all valid doctor names first
    cursor.execute("SELECT DISTINCT doctor_name FROM schedule")
    all_doctors = [row[0] for row in cursor.fetchall()]
    
    # 2. Fuzzy Match: Find the closest name to what user typed
    # extractOne returns ('Dr. Sharma', 90) -> (Name, Score)
    best_match, score = process.extractOne(query_name, all_doctors)
    
    print(f"🔍 Fuzzy Search: '{query_name}' matched with '{best_match}' (Score: {score})")
    
    if score < 70: # If similarity is too low, assume not found
        conn.close()
        return None

    # 3. Fetch details for that matched doctor
    cursor.execute("SELECT department, day, availability FROM schedule WHERE doctor_name=?", (best_match,))
    rows = cursor.fetchall()
    conn.close()
    
    return {"name": best_match, "schedule": rows}