import requests
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

def get_coordinates(address):
    geolocator = Nominatim(user_agent="ai-realtor")
    location = geolocator.geocode(address)
    return (location.latitude, location.longitude) if location else (None, None)

def get_nearby_places(lat, lon, place_type):
    url = f"https://api.geoapify.com/v2/places?categories={place_type}&filter=circle:{lon},{lat},2000&limit=5&apiKey={GEOAPIFY_API_KEY}"
    res = requests.get(url)
    if res.status_code == 200:
        places = []
        for p in res.json().get('features', []):
            props = p.get('properties', {})
            places.append({
                "name": props.get('name', 'Unnamed Place'),
                "address": props.get('formatted', 'No address'),
                "distance": int(props.get('distance', 0)),
                "category": props.get('categories', [''])[0]
            })
        return places
    return []

def get_neighborhood_info(address):
    lat, lon = get_coordinates(address)
    if lat is None:
        print("Failed to get coordinates.")
        return None

    return {
        "Schools": get_nearby_places(lat, lon, "education.school"),
        "Restaurants": get_nearby_places(lat, lon, "catering.restaurant"),
        "Hospitals": get_nearby_places(lat, lon, "healthcare.hospital")
    }

def build_neighborhood_summary(info):
    def format_place(p):
        return f"{p['name']} - {p['address']} ({p['category']}, {p['distance']}m)"

    summary_lines = []
    for category, places in info.items():
        summary_lines.append(f"\n{category}:")
        if places:
            for p in places:
                summary_lines.append(f"  - {format_place(p)}")
        else:
            summary_lines.append("  - No notable places found nearby.")
    return "\n".join(summary_lines)

def save_summary_to_file(summary, filename="neighborhood_summary.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"Neighborhood summary saved to {filename}")

