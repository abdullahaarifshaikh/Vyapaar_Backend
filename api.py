import os
import tempfile
import requests
from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import VERIFY_TOKEN, WHATSAPP_TOKEN, PHONE_NUMBER_ID
from core.workflow import build_workflow
from main import SYSTEM_PROMPT
from tools.audio_tools import process_audio_file

app = FastAPI()
agent_app = build_workflow()

# State management (In production, map this by user phone number for distinct sessions)
messages_store = {}

@app.get("/webhook")
async def verify_webhook(
        hub_mode: str = Query(..., alias="hub.mode"),
        hub_verify_token: str = Query(..., alias="hub.verify_token"),
        hub_challenge: str = Query(..., alias="hub.challenge")):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge, status_code=200)
    return PlainTextResponse(content="Verification failed", status_code=403)

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value:
            message_data = value["messages"][0]
            sender_id = message_data["from"]

            if message_data["type"] == "text":
                user_text = message_data["text"]["body"]
                
                # Setup session history per user
                if sender_id not in messages_store:
                    messages_store[sender_id] = [SystemMessage(content=SYSTEM_PROMPT)]

                response = process_with_ai(sender_id, user_text)
                send_whatsapp_message(sender_id, response)

            elif message_data["type"] == "audio":
                audio_id = message_data["audio"]["id"]
                audio_path = download_whatsapp_media(audio_id)
                
                if audio_path:
                    # Use the tool to transcribe and translate
                    result = process_audio_file.invoke({"audio_file_path": audio_path})
                    
                    if result.get("status") == "success":
                        user_text = result.get("translated_text", "")
                        
                        if user_text:
                            # Setup session history per user
                            if sender_id not in messages_store:
                                messages_store[sender_id] = [SystemMessage(content=SYSTEM_PROMPT)]

                            response = process_with_ai(sender_id, user_text)
                            send_whatsapp_message(sender_id, response)
                    
                    # Cleanup temp file
                    if os.path.exists(audio_path):
                        os.remove(audio_path)

    except Exception as e:
        print(f"Error processing message: {e}")
        return {"status": "error", "error": str(e)}

    return {"status": "received"}

def process_with_ai(sender_id: str, user_input: str) -> str:
    user_history = messages_store[sender_id]
    user_history.append(HumanMessage(content=user_input))

    result = agent_app.invoke({"messages": user_history})
    last_message = result["messages"][-1]
    
    user_history.append(last_message)
    return last_message.content

def send_whatsapp_message(to_number: str, message_text: str):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }
    requests.post(url, json=payload, headers=headers)

def download_whatsapp_media(media_id: str) -> str:
    """Downloads media from WhatsApp and returns the local file path."""
    try:
        # Step 1: Get media URL
        url = f"https://graph.facebook.com/v17.0/{media_id}"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        response = requests.get(url, headers=headers)
        media_url = response.json().get("url")
        
        if not media_url:
            print(f"Could not get URL for media {media_id}")
            return None
            
        # Step 2: Download the file
        media_response = requests.get(media_url, headers=headers)
        
        # Create a temp file
        # Most WhatsApp audio messages are .ogg or .m4a
        processed_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
        processed_file.write(media_response.content)
        processed_file.close()
        
        return processed_file.name
    except Exception as e:
        print(f"Error downloading WhatsApp media: {e}")
        return None
