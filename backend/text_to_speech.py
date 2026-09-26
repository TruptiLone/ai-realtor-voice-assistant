import requests
from decouple import config

ELEVEN_LABS_API_KEY = config("ELEVEN_LABS_API_KEY")

# ElevenLabs Text-to-Speech
def convert_text_to_speech(message: str) -> bytes | None:
    body = {
        "text": message,
        "voice_settings": {
            "stability": 0.3,
            "similarity_boost": 0.5
        }
    }

    voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel

    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }

    endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    try:
        response = requests.post(endpoint, json=body, headers=headers)
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx
        return response.content
    except requests.RequestException as e:
        print(f"[TTS ERROR] ElevenLabs request failed: {e}")
        return None
