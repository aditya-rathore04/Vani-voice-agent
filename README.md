# 🏥 Vani — The Multilingual AI Voice Receptionist

**Vani** is a Tier-A Agentic Voice System designed to bridge the digital divide in healthcare. It allows patients to enquire about doctor availability via **WhatsApp Voice Notes** in their native language (Hindi, Malayalam, Kannada, English) without typing.

Behind the scenes, it features a **"God Mode" Admin Dashboard** that allows clinic staff to update schedules in real-time using voice commands or a web interface.

---

## 🚀 Features

### 🗣️ For Patients (Read-Only)
* **Voice-First Interface:** Users send voice notes; Vani replies with natural-sounding voice notes.
* **Polyglot Intelligence:** Automatically detects and speaks **English, Hindi, Kannada, and Malayalam**.
* **Medical Translation:** Understands colloquial terms like *"Dil ka doctor"* and maps them to *"Cardiologist"*.
* **Smart Availability:** Handles "Walk-in" logic (no complex booking slots, just "Available/Unavailable").

### 🔧 For Clinic Admin (Read-Write)
* **Web Dashboard:** A Streamlit-based UI to view logs and edit the schedule manually.
* **Voice Command ("God Mode"):** Admins can send voice notes like *"Mark Dr. Sharma as On Leave for Monday"* to update the database instantly.

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Brain (LLM)** | **Llama 3.3 (Groq)** | Ultra-low latency reasoning and tool usage. |
| **Ears (ASR)** | **faster-whisper** | Local, CPU-optimized speech-to-text (supports Indian languages). |
| **Mouth (TTS)** | **Edge-TTS** | High-quality Neural voice generation. |
| **Backend** | **FastAPI** | Asynchronous Python web server for Webhooks. |
| **Database** | **SQLite** | Lightweight, file-based relational database. |
| **Admin UI** | **Streamlit** | Data dashboard for clinic staff. |
| **Tunnel** | **Ngrok** | Exposes localhost to WhatsApp Cloud API. |

---

## ⚙️ Installation Guide

### 1. Prerequisites
* **Python 3.10+** installed.
* **FFmpeg** installed and added to System PATH (Required for audio processing).
* A **Meta Developer Account** (for WhatsApp API).
* A **Groq Cloud API Key** (Free tier).

### 2. Clone & Setup
```bash
# Clone the repository
git clone [https://github.com/YOUR_USERNAME/vani-voice-agent.git](https://github.com/YOUR_USERNAME/vani-voice-agent.git)
cd vani-voice-agent

# Create Virtual Environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt
```
### 3. Environment Configuration
Create a .env file in the root directory and add your keys:
```
# Meta / WhatsApp Credentials
VERIFY_TOKEN=vani_secret_123
WHATSAPP_TOKEN=EAAG... (Your Permanent Access Token)
PHONE_NUMBER_ID=123456...

# AI Credentials
GROQ_API_KEY=gsk_...

# Admin Security
ADMIN_PHONE=919999988888  (Your WhatsApp number with country code, no +)
```
### 4. Initialize Database
Run the seed script to create the clinic.db file with dummy data:
```
python init_db.py
```
## 🏃‍♂️ How to Run
You need to run three components simultaneously (use split terminals).

### Terminal 1: The Backend Server
```
uvicorn app.main:app --reload
```
### Terminal 2: The Secure Tunnel
```
ngrok http 8000
```
Copy the Forwarding URL (e.g., https://xyz.ngrok-free.app) and update your Meta App Dashboard -> WhatsApp -> Configuration -> Webhook URL.
### Terminal 3: The Admin Dashboard
```
streamlit run app/admin.py
```

##🧪 Usage Examples
### Patient Mode (Any Number)
* 🎤 Voice Note: "Is Dr. Sharma available tomorrow?"

* 🤖 Reply: "Dr. Sharma (Cardiology) is available tomorrow from 10 AM to 2 PM."

### Admin Mode (From ADMIN_PHONE only)
* 🎤 Voice Note: "Mark Dr. Sharma as On Leave for Monday."

* 🤖 Text Reply: "✅ Updated Dr. Sharma's status to: ON LEAVE"

## 📂 Project Structure
```
/vani-voice-agent
├── app/
│   ├── main.py              # FastAPI Webhook Entry Point
│   ├── ai_engine.py         # Llama 3 Logic & Prompt Engineering
│   ├── audio.py             # Whisper (ASR) & Edge-TTS Logic
│   ├── database.py          # SQLite Query & Fuzzy Matching
│   ├── admin.py             # Streamlit Dashboard UI
│   ├── admin_ai.py          # Admin Command Logic
│   └── whatsapp_client.py   # WhatsApp API Wrapper
├── data/                    # Database & Temp Audio Files
├── init_db.py               # Database Seeding Script
├── requirements.txt         # Project Dependencies
└── README.md                # Project Documentation
