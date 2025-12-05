# app/whatsapp_client.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("PHONE_NUMBER_ID")

def get_media_url(media_id):
    """ Get the download link for the user's audio """
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.json().get("url")

def download_media_file(media_url, save_path):
    """ Download the user's audio to our laptop """
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(media_url, headers=headers)
    with open(save_path, "wb") as f:
        f.write(response.content)
    return save_path

def upload_media(file_path):
    """ Upload our OGG reply to WhatsApp """
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/media"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # MIME type for OGG Voice Note
    mime_type = "audio/ogg" 
    
    files = {
        'file': (os.path.basename(file_path), open(file_path, 'rb'), mime_type)
    }
    data = {'messaging_product': 'whatsapp'}
    
    response = requests.post(url, headers=headers, files=files, data=data)
    return response.json().get("id")

def send_whatsapp_audio(to_number, media_id):
    """ Send the uploaded audio as a reply """
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "audio",
        "audio": {"id": media_id}
    }
    
    requests.post(url, headers=headers, json=data)

# Keep the text sending function too
def send_whatsapp_message(to_number, text_body):
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": text_body}}
    requests.post(url, headers=headers, json=data)