# app/audio.py
import os
import edge_tts
from faster_whisper import WhisperModel
from pydub import AudioSegment

# 1. SETUP WHISPER (The Ears)
print("⏳ Loading Whisper Model...")
# CHANGE: Upgraded from "tiny" to "small"
model = WhisperModel("small", device="cpu", compute_type="int8")
print("✅ Whisper (Small) Loaded!")

# VOICE MAPPING (The Dictionary)
VOICE_MAP = {
    "en": "en-IN-NeerjaNeural",  # Indian English
    "hi": "hi-IN-SwaraNeural",   # Hindi
    "kn": "kn-IN-SapnaNeural",   # Kannada
    "ml": "ml-IN-SobhanaNeural"  # Malayalam
}

def transcribe_audio(file_path):
    """
    Returns tuple: (text, language_code)
    """
    try:
        segments, info = model.transcribe(file_path, beam_size=1)
        text = " ".join([segment.text for segment in segments])
        
        # Whisper automatically detects language (e.g., 'hi', 'kn')
        detected_lang = info.language
        print(f"🌍 Detected Language: {detected_lang}")
        
        return text.strip(), detected_lang
    except Exception as e:
        print(f"❌ Transcribe Error: {e}")
        return "", "en"

# 2. SETUP TTS (The Mouth)
async def generate_voice_note(text, language_code, output_ogg_path):
    """
    Uses the correct voice based on language_code
    """
    temp_mp3 = "data/temp_tts.mp3"
    
    # Select Voice (Default to English if language not found)
    selected_voice = VOICE_MAP.get(language_code, "en-IN-NeerjaNeural")
    print(f"👄 Speaking in: {selected_voice}")

    # Remove newlines and excess spaces that crash Edge-TTS
    clean_text = " ".join(text.split()) 
    
    if not clean_text:
        print("❌ Error: TTS received empty text.")
        return None

    # ... (Rest of the function logic: Select Voice, Communicate, Convert) ...
    
    communicate = edge_tts.Communicate(clean_text, selected_voice)
    await communicate.save(temp_mp3)
    
    # Convert to OGG
    try:
        audio = AudioSegment.from_mp3(temp_mp3)
        audio.export(output_ogg_path, format="ogg", codec="libopus")
    except Exception as e:
        print(f"❌ Audio Conversion Error: {e}")
    
    if os.path.exists(temp_mp3):
        os.remove(temp_mp3)
        
    return output_ogg_path