import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load API key from .env
load_dotenv()
api_key = os.getenv("ELEVEN_LABS_API_KEY")
if not api_key:
    raise ValueError("Missing ELEVEN_LABS_API_KEY in environment variables.")

# Initialize ElevenLabs client
client = ElevenLabs(api_key=api_key)

# Set paths
script_folder = os.path.join(os.getenv("PROPERTIES_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "properties"))), "Property101", "HouseTour", "room_scripts")
voice_id = "JBFqnCBsd6RMkjVDRZzb"  # Replace with desired voice ID
model_id = "eleven_multilingual_v2"

# Output audio files here
output_folder = os.path.join(script_folder, "audio")
os.makedirs(output_folder, exist_ok=True)

# Loop through text files and convert to audio
for filename in os.listdir(script_folder):
    if filename.endswith(".txt"):
        input_path = os.path.join(script_folder, filename)
        print(f"Generating audio for: {filename}")

        try:
            with open(input_path, "r", encoding="utf-8") as f:
                text = f.read().strip()

            # Convert text to audio (returns generator/stream)
            stream = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                output_format="mp3_44100_128",
            )

            # Save stream as audio file
            audio_path = os.path.join(output_folder, filename.replace(".txt", ".mp3"))
            with open(audio_path, "wb") as audio_file:
                for chunk in stream:
                    audio_file.write(chunk)

            print(f"Saved: {audio_path}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")
