"""
Maps PRO lookup (Google Places Nearby Search).
"""
from __future__ import annotations
import os, re, requests
from typing import Dict, List, Tuple
import math
from dotenv import load_dotenv

load_dotenv()
MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
assert MAPS_KEY, "Set GOOGLE_MAPS_API_KEY in .env"

# ---------- 1. classify the trade ----------
SERVICE_MAP: dict[str, str] = {
    r"(smoke|fire.*alarm|wiring|circuit|breaker|socket)": "electrician",
    r"(leak|pipe|faucet|sink|toilet|sewer)":             "plumber",
    r"(hvac|air.?condition|furnace|vent)":               "hvac_contractor",
    r"(roof|shingle|gutter)":                            "roofing_contractor",
    r"(appliance|fridge|washer|dryer)":                  "appliance_store",
    r".*":                                               "general_contractor",
}
def choose_place_type(text: str) -> str:
    for pat, ptype in SERVICE_MAP.items():
        if re.search(pat, text, re.I):
            return ptype
    return "general_contractor"


# ---------- 2. geocode plain address ----------
def geocode(addr: str) -> Tuple[float, float]:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    r = requests.get(url, params={"address": addr, "key": MAPS_KEY}, timeout=5).json()
    loc = r["results"][0]["geometry"]["location"]
    return loc["lat"], loc["lng"]


# ---------- 3. parse "lat,lng" helper ----------
def parse_location_string(s: str) -> Tuple[float, float]:
    lat, lng = map(float, s.split(","))
    return lat, lng




# ---------- 4. nearby contractors with distance ----------
def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points (in km)."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def find_nearby_pros(
    place_type: str,
    lat: float,
    lng: float,
    radius_m: int = 8000,
    top_k: int = 5,
) -> List[Dict]:
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius_m,
        "type": place_type,
        "key": MAPS_KEY,
    }
    res = requests.get(url, params=params, timeout=5).json().get("results", [])
    res.sort(key=lambda x: x.get("rating", 0), reverse=True)
    picks = res[: top_k]
    out = []
    for p in picks:
        pro_lat = p["geometry"]["location"]["lat"]
        pro_lng = p["geometry"]["location"]["lng"]
        distance_km = haversine(lat, lng, pro_lat, pro_lng)
        out.append({
            "name": p["name"],
            "rating": p.get("rating", "—"),
            "vicinity": p.get("vicinity"),
            "maps_url": f"https://www.google.com/maps/place/?q=place_id:{p['place_id']}",
            "distance_km": distance_km,
        })
    return out