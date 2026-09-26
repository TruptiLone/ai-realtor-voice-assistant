import os
import re
import openai
from dotenv import load_dotenv

# Load API keys and environment variables from .env file
load_dotenv()
api_key = os.getenv("OPEN_AI_KEY")
if not api_key:
    raise ValueError("Missing OPEN_AI_KEY in environment variables.")

# Initialize OpenAI client
client = openai.OpenAI(api_key=api_key)

# Define paths
BASE_PATH = os.getenv("PROPERTIES_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "properties")))
PROPERTY_ID = "Property101"

# File paths for input
property_details_path = os.path.join(BASE_PATH, PROPERTY_ID, "property_details.txt")
room_descriptions_path = os.path.join(BASE_PATH, PROPERTY_ID, "RealtorChat", "room_description.txt")

# Output directory for generated scripts
output_dir = os.path.join(BASE_PATH, PROPERTY_ID, "HouseTour", "room_scripts")
os.makedirs(output_dir, exist_ok=True)

# Read the property overview text
with open(property_details_path, "r", encoding="utf-8") as f:
    property_info = f.read().strip()

# Read the room descriptions text
with open(room_descriptions_path, "r", encoding="utf-8") as f:
    room_data = f.read()

# Extract room blocks using regex. Each room section starts with === Room Name ===
room_blocks = re.findall(r"===\s*(.*?)\s*===\s*(.*?)(?===|$)", room_data, re.DOTALL)

# Function to generate a short welcome script for the home tour
def generate_welcome_script(property_info: str, room_description: str) -> str:
    prompt = f"""
You are a friendly and knowledgeable virtual real estate tour guide. Your task is to generate a short 3–5 line welcome script at the start of a smart home tour.

Content to include:
- Overall square footage or layout feel
- Notable features of the house (e.g., number of bedrooms, backyard, natural light)
- Mention the community or nearby amenities if available
- Keep it warm, natural, and brief — like the start of a narrated tour

Property Overview:
{property_info}

Room Descriptions (sampled):
{room_description[:1000]}

Now write a short welcome script that could be spoken at the start of the tour.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

# Function to generate a room-specific tour script
def generate_room_script(property_info, room_name, room_description):
    prompt = f"""
You are a friendly, knowledgeable virtual tour guide for a modern smart home. Your task is to generate room-by-room walkthrough scripts using:

1. A high-level property overview
2. Room-specific visual descriptions
3. Visual features like "sliding glass doors", "recessed lighting", "fireplace"
4. Floorplan flow, if provided

Guidelines:
- Speak naturally and clearly, like you're guiding someone in person
- Use simple, friendly language
- Include directional phrases like “To your left...”, “Straight ahead...”, etc.
- Mention key visual or architectural features
- End each script with a smooth transition to the next logical space

Property Overview:
{property_info}

Room Name:
{room_name}

Room Description:
{room_description}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# Step 1: Generate and save the welcome script
print("Generating welcome script...")
welcome_script = generate_welcome_script(property_info, room_data)
welcome_path = os.path.join(output_dir, "welcome.txt")
with open(welcome_path, "w", encoding="utf-8") as f:
    f.write(welcome_script)
print(f"Welcome script saved at: {welcome_path}")

# Step 2: Generate and save scripts for each room
for room_name, room_description in room_blocks:
    room_clean = room_name.strip().lower().replace(" ", "_")
    print(f"Generating script for room: {room_name}")
    script = generate_room_script(property_info, room_name.strip(), room_description.strip())

    # Save each room script as a text file
    text_path = os.path.join(output_dir, f"{room_clean}.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(script)
    print(f"Room script saved at: {text_path}")
