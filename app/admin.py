# app/admin.py
import streamlit as st
import sqlite3
import pandas as pd
import time

st.set_page_config(page_title="Vani Clinic Admin", layout="wide")

DB_PATH = "data/clinic.db"

# --- HELPER FUNCTIONS ---
def load_schedule():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM schedule", conn)
    conn.close()
    return df

def save_schedule(edited_df):
    conn = sqlite3.connect(DB_PATH)
    # Replace the old table with the new edited one
    edited_df.to_sql("schedule", conn, if_exists="replace", index=False)
    conn.close()

# --- UI LAYOUT ---
st.title("🏥 City Health Clinic - Control Center")

tab1, tab2 = st.tabs(["📅 Manage Schedule", "💬 Live Logs"])

# === TAB 1: SCHEDULE MANAGER ===
with tab1:
    st.header("Doctor Availability")
    st.info("Double-click any cell to edit. Click 'Save Changes' to update the bot instantly.")
    
    # Load current data
    df = load_schedule()
    
    # Show editable grid
    edited_df = st.data_editor(
        df,
        num_rows="dynamic", # Allow adding new doctors
        key="schedule_editor"
    )
    
    # Save Button
    if st.button("💾 Save Changes", type="primary"):
        save_schedule(edited_df)
        st.success("✅ Database Updated! Vani will now use this new schedule.")
        time.sleep(1)
        st.rerun()

# === TAB 2: LIVE LOGS ===
with tab2:
    st.header("Recent Conversations")
    
    # We don't have a database for logs yet (we used in-memory list),
    # so for now, we will just show a placeholder or read from a log file if we add one.
    # For Phase 4, let's just show the Schedule logic first.
    st.warning("Live logs require a persistent database (coming in v2).")
    
    # Optional: You can create a 'logs' table in SQLite later to populate this.