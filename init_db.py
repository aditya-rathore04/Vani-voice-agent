# init_db.py
import sqlite3
import os

os.makedirs("data", exist_ok=True)
DB_PATH = "data/clinic.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS schedule")
    
    # NEW SCHEMA: Separate Time and Status
    cursor.execute("""
    CREATE TABLE schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_name TEXT,
        department TEXT,
        day TEXT,
        schedule_time TEXT,       -- e.g., "10:00 AM - 02:00 PM" (Fixed)
        current_status TEXT DEFAULT 'Available' -- e.g., "Available", "On Leave", "Emergency"
    )
    """)
    
    # Data now maps to (name, dept, day, schedule_time)
    # status defaults to 'Available' automatically
    doctors = [
        ("Dr. Sharma", "Cardiology", "Monday", "10:00 AM - 02:00 PM"),
        ("Dr. Sharma", "Cardiology", "Wednesday", "10:00 AM - 02:00 PM"),
        ("Dr. Gupta", "Dermatology", "Tuesday", "09:00 AM - 05:00 PM"),
        ("Dr. Gupta", "Dermatology", "Friday", "09:00 AM - 01:00 PM"),
        ("Dr. Anjali", "General", "Daily", "08:00 AM - 08:00 PM"),
        ("Dr. Khan", "Neurology", "Thursday", "04:00 PM - 08:00 PM")
    ]
    
    cursor.executemany("INSERT INTO schedule (doctor_name, department, day, schedule_time) VALUES (?, ?, ?, ?)", doctors)
    
    conn.commit()
    conn.close()
    print(f"✅ Database upgrade complete: Added 'current_status' column.")

if __name__ == "__main__":
    init_db()