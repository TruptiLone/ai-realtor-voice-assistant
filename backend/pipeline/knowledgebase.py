import openai
import os
import json
from PIL import Image
from io import BytesIO
import base64
from dotenv import load_dotenv

from neighborhooddata import (
    get_neighborhood_info,
    build_neighborhood_summary,
    save_summary_to_file
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPEN_AI_KEY")
if not api_key:
    raise ValueError("Missing OPEN_AI_KEY in environment variables.")
client = openai.OpenAI(api_key=api_key)

# Property summary prompt
PROPERTY_PROMPT = """
You are a friendly and knowledgeable virtual real estate assistant helping to create a conversational knowledge base for a home listing. Based on the content provided, extract key insights that can be used to answer common questions from potential buyers in a gentle, helpful tone.
Please address only the topics where the information is clearly available. Avoid guessing or assuming details. If something isn't mentioned, simply leave it out—no need to speculate or make up details.
Here are the key areas to focus on:
1. Public Schools Nearby: If available, mention nearby public schools by name. You may include distances and ratings, but only if they are provided.
2. Private Schools: Mention any nearby private schools only if listed.
3. Transportation Options: Describe nearby bus or train stations, and major highways or freeways mentioned in the content.
4. Neighborhood Safety: Summarize safety info only if crime rates or safety details are explicitly stated.
5. Noise Levels: Talk about noise levels if there’s relevant context (like freeways, stadiums, or descriptions of the area being quiet).
6. County and Zoning: Provide county and zoning classification if included.
7. Property Specifications: Include number of bedrooms and bathrooms, square footage, lot size, year built, number of stories, and any bonus rooms.
8. Renovation History: Mention any recent updates or remodeling, such as electrical, plumbing, kitchen, bathrooms, etc.
9. Utility Information: Describe available utilities and whether they are public or private—only if mentioned.
10. Nearby Amenities: List nearby parks, gyms, grocery stores, hospitals, and notable tech or entertainment landmarks.
11. Construction Activity: Only include if any current or planned construction projects are mentioned.
12. Room Descriptions: Provide a tour-style description of the rooms using a warm, conversational tone. Focus on layout, size, lighting, window placement, and flow. Avoid furniture details.
Structure your response so that each section feels like a natural, helpful answer a homebuyer might hear. Be clear, warm, and conversational.
"""

# Image captioning prompt
ROOM_IMAGE_PROMPT = """
You are a helpful virtual home assistant guiding a house tour. Describe the room shown in this image.
Focus on the layout, size, window placement, natural lighting, flow between spaces, and the overall ambiance.
Avoid describing furniture—emphasize architectural features, space utilization, and how the room might feel to walk through.
Keep the tone factual, friendly, and tour-style. Keep your response concise: no more than 3–5 sentences.
"""



# Convert image to base64 for OpenAI API input
def image_to_base64(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        raise ValueError(f"Could not open image {image_path}: {e}")
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Generate room description from image
def generate_description(image_path):
    img_b64 = image_to_base64(image_path)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ROOM_IMAGE_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_b64}"
                        }
                    }
                ]
            }
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# Extract address from property details text file
property_address = None
def fetch_address_from_text_file(property_details_file):
    global property_address
    try:
        with open(property_details_file, 'r') as file:
            for line in file:
                if line.strip().startswith("Address:"):
                    property_address = line.strip().split("Address:", 1)[1].strip()
                    break
        if property_address is None:
            return "Address not found in file."
        return property_address
    except FileNotFoundError:
        return "Property details file not found."
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Generate neighborhood summary and write to file
def generate_neighborhood_summary_file(address, output_dir="output", filename="neighborhood_summary.txt"):
    info = get_neighborhood_info(address)
    if not info:
        print("Neighborhood info not found.")
        return
    summary = build_neighborhood_summary(info)
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"Neighborhood summary saved to {file_path}")

# Summarize property details using OpenAI
def summarize_property_details(property_txt_path, output_dir):
    with open(property_txt_path, "r", encoding="utf-8") as f:
        property_text = f.read()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": PROPERTY_PROMPT},
            {"role": "user", "content": property_text}
        ],
        temperature=0.4
    )
    summary = response.choices[0].message.content.strip()
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "property_summary.txt")
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(summary)
    print(f"Property summary saved at: {output_path}")

# Folder paths
import os

# Folder paths
BASE_PATH = os.getenv("PROPERTIES_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "properties")))
PROPERTY_ID = "Property101"
IMAGES_FOLDER = os.path.join(BASE_PATH, PROPERTY_ID, "Images")

# Example placeholder for actual image description function
def generate_description(image_path):
    img_b64 = image_to_base64(image_path)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ROOM_IMAGE_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_b64}"
                        }
                    }
                ]
            }
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()


# Generate descriptions for each room image in subfolders
def generate_room_descriptions(property_id, images_folder):
    if not os.path.exists(images_folder):
        raise Exception(f"Main folder does not exist: {images_folder}")
    
    realtorchat_folder = os.path.join(BASE_PATH, property_id, "RealtorChat")
    os.makedirs(realtorchat_folder, exist_ok=True)  # Ensure folder exists

    output_file = os.path.join(realtorchat_folder, "room_description.txt")
    print(f"Creating/Opening output file at: {output_file}")

    print(f"Creating/Opening output file at: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as out_file:
        for room_folder in sorted(os.listdir(images_folder)):
            room_path = os.path.join(images_folder, room_folder)
            if os.path.isdir(room_path):
                print(f"Processing Room: {room_folder}")
                out_file.write(f"=== {room_folder} ===\n\n")
                for filename in sorted(os.listdir(room_path)):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        image_path = os.path.join(room_path, filename)
                        try:
                            print(f"  - Describing: {filename}")
                            desc = generate_description(image_path)
                            print(f"  - Description: {desc}")
                            out_file.write(f"{filename}:\n{desc}\n\n")
                        except Exception as e:
                            print(f"  Error with {filename}: {e}")

# Master function to process a full property folder
def process_property(property_id, root_dir="PracticumProject"):
    property_folder = os.path.join(root_dir, property_id)
    images_folder = os.path.join(property_folder, "Images")
    realtorchat_folder = os.path.join(property_folder, "RealtorChat")
    property_details_path = os.path.join(realtorchat_folder, "property_details.txt")

    if not os.path.exists(property_folder):
        raise Exception(f"Property folder not found: {property_folder}")

    print(f"Processing property: {property_id}")

    # 1. Generate property summary
    print("Generating property summary...")
    summarize_property_details(property_details_path, output_dir=realtorchat_folder)

    # 2. Extract address and generate neighborhood summary
    print("Extracting address and generating neighborhood summary...")
    address = fetch_address_from_text_file(property_details_path)
    if address and not address.startswith("Address not found"):
        generate_neighborhood_summary_file(address, output_dir=realtorchat_folder)
    else:
        print("Address not found; skipping neighborhood summary.")

    # 3. Generate room descriptions from image folders
    print("Generating room descriptions...")
    generate_room_descriptions(property_id=property_id, images_folder=images_folder)


# Entry point for CLI execution
if __name__ == "__main__":
    import sys
    property_id = sys.argv[1] if len(sys.argv) > 1 else "Property101"
    process_property(property_id, root_dir=BASE_PATH)
