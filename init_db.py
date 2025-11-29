# init_db.py
import sqlite3
import os

# Ensure the data folder exists
os.makedirs("data", exist_ok=True)
DB_PATH = "data/clinic.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Reset: Drop old tables if they exist (Fresh start)
    cursor.execute("DROP TABLE IF EXISTS schedule")
    
    # 2. Create Table: Simple structure for an Enquiry Bot
    cursor.execute("""
    CREATE TABLE schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_name TEXT,
        department TEXT,
        day TEXT,
        availability TEXT
    )
    """)
    
    # 3. Add Dummy Data (Indian Context)
    doctors = [
        ("Dr. Sharma", "Cardiology", "Monday", "10:00 AM - 02:00 PM"),
        ("Dr. Sharma", "Cardiology", "Wednesday", "10:00 AM - 02:00 PM"),
        ("Dr. Gupta", "Dermatology", "Tuesday", "09:00 AM - 05:00 PM"),
        ("Dr. Gupta", "Dermatology", "Friday", "09:00 AM - 01:00 PM"),
        ("Dr. Anjali", "General", "Daily", "08:00 AM - 08:00 PM"),
        ("Dr. Khan", "Neurology", "Thursday", "04:00 PM - 08:00 PM")
    ]
    
    cursor.executemany("INSERT INTO schedule (doctor_name, department, day, availability) VALUES (?, ?, ?, ?)", doctors)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH} with {len(doctors)} entries.")

if __name__ == "__main__":
    init_db()