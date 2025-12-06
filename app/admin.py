# app/admin.py
import streamlit as st
import sqlite3
import pandas as pd
import time

st.set_page_config(page_title="Vani Clinic Admin", layout="wide", page_icon="🏥")

DB_PATH = "data/clinic.db"

# --- HELPER FUNCTIONS ---
def load_schedule():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM schedule", conn)
    conn.close()
    return df

def save_schedule(edited_df):
    conn = sqlite3.connect(DB_PATH)
    edited_df.to_sql("schedule", conn, if_exists="replace", index=False)
    conn.close()

# --- UI LAYOUT ---
st.title("🏥 City Health Clinic - Control Center")
st.markdown("---")

# METRICS ROW (Visual Appeal)
col1, col2, col3 = st.columns(3)
df = load_schedule()
total_docs = df['doctor_name'].nunique()
on_leave = df[df['current_status'] == "ON LEAVE"].shape[0]

col1.metric("Total Doctors", total_docs)
col2.metric("Active Shifts", df.shape[0])
col3.metric("Doctors On Leave", on_leave, delta_color="inverse")

# --- TAB INTERFACE ---
tab1, tab2 = st.tabs(["📅 Manage Schedule", "💬 Live Logs"])

# === TAB 1: SCHEDULE MANAGER ===
with tab1:
    st.subheader("Doctor Availability Manager")
    st.info("💡 Tip: Use the 'Status' dropdown to quickly mark attendance.")
    
    # ADVANCED EDITOR
    # We configure specific columns to be read-only or dropdowns
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key="schedule_editor",
        column_config={
            "id": st.column_config.NumberColumn(disabled=True), # Lock ID
            "doctor_name": st.column_config.TextColumn("Doctor Name"),
            "department": st.column_config.TextColumn("Specialty"),
            "schedule_time": st.column_config.TextColumn(
                "Shift Timings",
                help="e.g. 10:00 AM - 02:00 PM"
            ),
            "current_status": st.column_config.SelectboxColumn(
                "Current Status",
                help="Is the doctor in today?",
                width="medium",
                options=[
                    "Available",
                    "ON LEAVE",
                    "Delayed (1 hr)",
                    "Emergency Leave"
                ],
                required=True
            )
        }
    )
    
    # Save Button
    if st.button("💾 Save Changes", type="primary"):
        save_schedule(edited_df)
        st.success("✅ Database Updated Successfully!")
        time.sleep(1)
        st.rerun()

# === TAB 2: LIVE LOGS ===
with tab2:
    st.header("Recent Conversations")
    st.warning("Feature coming soon: Persistent Log Database integration.")
    st.markdown("*Currently, logs are visible in the VS Code Terminal.*")