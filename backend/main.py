# main.py (merged)

import os
import io
import json
import base64
import logging
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
import soundfile as sf
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import AsyncCallbackHandler
from speech_to_text import transcribe_audio_file
from text_to_speech import convert_text_to_speech
from RealtorAssistantRag import load_qa_chain_for_property
from decouple import config

# Load environment variables
OPENAI_API_KEY = config("OPEN_AI_KEY")
if not OPENAI_API_KEY:
    raise ValueError("[FATAL] OPEN_AI_KEY not loaded from .env")

# Setup FastAPI
app = FastAPI()

# Setup CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mount static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
PROPERTY_DIR = os.getenv("PROPERTIES_DIR", os.path.join(PROJECT_ROOT, "data", "properties"))

app.mount("/static", StaticFiles(directory=PROPERTY_DIR), name="static")

# ---------- 🏠 House Tour Endpoints ----------

@app.get("/properties")
def get_properties():
    listings = []

    for folder in os.listdir(PROPERTY_DIR):
        folder_path = os.path.join(PROPERTY_DIR, folder)
        tour_path = os.path.join(folder_path, "HouseTour")
        info_path = os.path.join(tour_path, "info.json")
        image_path = os.path.join(tour_path, "Entrance.webp")

        if os.path.isdir(folder_path) and os.path.exists(info_path):
            with open(info_path, "r") as f:
                data = json.load(f)
                data["id"] = int(folder.replace("Property", ""))
                data["imageUrl"] = f"/static/{folder}/HouseTour/Entrance.webp"
                listings.append(data)

    return JSONResponse(content=sorted(listings, key=lambda x: x["id"]))


@app.get("/tour/{property_id}")
def get_property_tour(property_id: int):
    folder = f"Property{property_id}"
    house_tour_dir = os.path.join(PROPERTY_DIR, folder, "HouseTour")
    tour_json_path = os.path.join(house_tour_dir, "tour.json")

    if not os.path.exists(tour_json_path):
        raise HTTPException(status_code=404, detail="Tour data not found.")

    with open(tour_json_path, "r") as f:
        raw_data = json.load(f)

    base_audio_url = f"/static/{folder}/HouseTour/room_scripts/audio"
    base_image_url = f"/static/{folder}/Images"

    response = {
        "id": property_id,
        "welcomeAudioUrl": f"{base_audio_url}/{raw_data.get('welcomeAudio')}",
        "rooms": []
    }

    for room in raw_data["rooms"]:
        room_name = room["name"].replace(" ", "")
        image_urls = []
        room_image_dir = os.path.join(PROPERTY_DIR, folder, "Images", room_name)
        if os.path.exists(room_image_dir):
            for img in os.listdir(room_image_dir):
                if img.endswith(".webp"):
                    image_urls.append(f"{base_image_url}/{room_name}/{img}")

        audio_url = f"{base_audio_url}/{room.get('audio')}" if room.get("audio") else None

        response["rooms"].append({
            "name": room["name"],
            "description": room["description"],
            "audioUrl": audio_url,
            "imageUrls": image_urls
        })

    return JSONResponse(content=response)


# ---------- 🤖 Voice Chatbot WebSocket ----------

class WebSocketStreamHandler(AsyncCallbackHandler):
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def on_llm_new_token(self, token: str, **kwargs):
        await self.websocket.send_text(json.dumps({"type": "token", "data": token}))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    audio_chunks = bytearray()
    stream_handler = WebSocketStreamHandler(websocket)
    property_id = None
    qa_chain = None

    try:
        while True:
            message = await websocket.receive()

            if "text" in message:
                try:
                    msg_data = json.loads(message["text"])
                    if msg_data.get("type") == "init":
                        property_id = msg_data.get("property_id")
                        qa_chain = load_qa_chain_for_property(property_id)
                        print(f"✅ Loaded QA chain for Property ID: {property_id}")
                        continue
                except Exception as e:
                    await websocket.send_text(json.dumps({"type": "error", "message": f"Init error: {str(e)}"}))
                    continue

            if "bytes" in message:
                audio_chunks.extend(message["bytes"])

                if len(audio_chunks) >= 5000 and qa_chain:
                    try:
                        with io.BytesIO(audio_chunks) as audio_io:
                            data, samplerate = sf.read(audio_io)
                            with io.BytesIO() as wav_buffer:
                                sf.write(wav_buffer, data, samplerate, format='WAV')
                                wav_bytes = wav_buffer.getvalue()

                        transcript = transcribe_audio_file(wav_bytes)
                        print("📥 Raw transcript received:", transcript)
                        print(f"📝 Transcript: {transcript}")
                        if not transcript.strip():
                            raise ValueError("Empty transcript")

                        await websocket.send_text(json.dumps({
                            "type": "user",
                            "text": transcript,
                            "property_id": property_id
                        }))

                        response = await qa_chain.ainvoke(transcript)
                        response_text = response.get("result", "")
                        print(f"🤖 Response: {response_text}")
                        audio_output = convert_text_to_speech(response_text)
                        encoded_audio = base64.b64encode(audio_output).decode("utf-8")

                        await websocket.send_text(json.dumps({
                            "type": "audio",
                            "text": response_text,
                            "audio_base64": encoded_audio,
                            "property_id": property_id
                        }))

                    except Exception as e:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Processing failed: {str(e)}"
                        }))

                    audio_chunks.clear()

    except WebSocketDisconnect:
        print("WebSocket disconnected.")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
