# app/utils/product_finder.py
import os
import requests
from typing import List, Dict, Optional
from math import radians, cos, sin, asin, sqrt

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """
    Calculate the great-circle distance between two points.
    """
    R = 6371  # Earth radius (km)
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def search_products(query: str, user_lat: float, user_lng: float) -> List[Dict[str, str]]:
    """
    Search for real products matching the query.
    Returns a list of product dicts with price, rating, store, and distance info.
    """
    url = "https://google.serper.dev/shopping"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "gl": "us"}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=8)
        products = resp.json().get("shopping", [])
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

    result = []
    for p in products:
        # Filtering: Must have at least title, link, price
        if "title" not in p or "link" not in p or "price" not in p:
            continue

        # Mock store location (since Google Shopping API doesn't return exact lat,lng yet)
        store_lat, store_lng = user_lat + 0.01, user_lng + 0.01  # simulate nearby
        distance_km = haversine_distance(user_lat, user_lng, store_lat, store_lng)

        result.append({
            "title": p["title"],
            "link": p["link"],
            "price": p.get("price", "N/A"),
            "rating": p.get("rating", "N/A"),
            "store": p.get("source", "Unknown Store"),
            "distance_km": round(distance_km, 2),
        })
    return result