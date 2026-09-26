from openai import OpenAI
from decouple import config
from typing import Optional

# Load OpenAI API key and initialize client
api_key = config("OPEN_AI_KEY")
if not api_key:
    raise ValueError("[FATAL] OPEN_AI_KEY not loaded from .env")

client = OpenAI(api_key=api_key)

# Unified transcription logic using OpenAI Whisper
def transcribe_audio_file(audio_data) -> Optional[str]:
    try:
        from io import BytesIO

        if isinstance(audio_data, (bytes, bytearray)):
            file_to_transcribe = BytesIO(audio_data)
            file_to_transcribe.name = "audio.webm"
        elif hasattr(audio_data, 'read'):
            file_to_transcribe = audio_data
            file_to_transcribe.seek(0)
        else:
            raise ValueError("Unsupported audio data type")

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=file_to_transcribe,
            response_format="text",
            language="en",
            temperature=0.2,
            prompt="This is a conversation about a property listing."
        )
        return transcript.strip() if transcript else None

    except Exception as e:
        print(f"[ERROR] Failed to transcribe audio: {e}")
        return None
    finally:
        if hasattr(audio_data, 'close'):
            try: audio_data.close()
            except: pass
