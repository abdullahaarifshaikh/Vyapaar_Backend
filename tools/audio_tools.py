import os
import mimetypes
from langchain_core.tools import tool
from sarvamai import SarvamAI
from config.settings import SARV_API

@tool
def process_audio_file(audio_file_path: str):
    """
    Transcribes and translates an audio file to English.
    Useful for processing voice messages in other languages.
    Args:
        audio_file_path: Path to the audio file on the local system.
    Returns:
        The translated text in English.
    """
    if not SARV_API:
        return {"status": "error", "message": "SARV_API key not configured."}

    if not os.path.exists(audio_file_path):
        return {"status": "error", "message": f"File not found: {audio_file_path}"}

    # --------- Content-Type Detection ---------
    extension_map = {
        '.m4a': 'audio/x-m4a',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.aac': 'audio/aac',
        '.flac': 'audio/flac',
        '.ogg': 'audio/ogg'
    }

    ext = os.path.splitext(audio_file_path)[1].lower()
    content_type = extension_map.get(ext) or mimetypes.guess_type(audio_file_path)[0] or "application/octet-stream"

    client = SarvamAI(api_subscription_key=SARV_API)

    try:
        # --------- Transcription ---------
        with open(audio_file_path, "rb") as f:
            response = client.speech_to_text.transcribe(
                file=(os.path.basename(audio_file_path), f, content_type),
                model="saaras:v3",
                mode="transcribe",
                language_code="unknown"  # Auto-detect language
            )

        transcript = response.transcript.strip()

        if not transcript:
            return {"status": "success", "message": "No speech detected in the audio file.", "translated_text": ""}

        # --------- Translation ---------
        translation_response = client.text.translate(
            input=transcript,
            source_language_code="auto",
            target_language_code="en-IN",
            speaker_gender="Male",
            mode="formal",
            model="mayura:v1",
            numerals_format="international"
        )

        # Extract translated text
        if hasattr(translation_response, "translated_text"):
            translated_text = translation_response.translated_text
        elif isinstance(translation_response, dict):
            translated_text = translation_response.get("translated_text", translation_response)
        else:
            translated_text = str(translation_response)

        return {
            "status": "success", 
            "original_transcript": transcript,
            "translated_text": translated_text
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
