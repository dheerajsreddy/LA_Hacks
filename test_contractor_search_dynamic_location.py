import os
import requests
import google.generativeai as genai
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

# Get API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PLACES_API_KEY = os.getenv("PLACES_API_KEY")

if not GEMINI_API_KEY or not PLACES_API_KEY:
    print("Error: API keys not found. Set GEMINI_API_KEY and PLACES_API_KEY in .env")
    sys.exit(1)

SEARCH_RADIUS_METERS = 15 * 1609 # 15 miles in meters

# --- Geocoding Function ---

def geocode_location(api_key: str, address: str) -> tuple[float, float] | None:
    """
    Uses Google Geocoding API to convert an address string into latitude/longitude.
    """
    print(f"\n[Geocoding] Attempting to find coordinates for: '{address}'")
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': api_key
    }
    try:
        response = requests.get(geocode_url, params=params, timeout=10)
        response.raise_for_status()
        results_data = response.json()

        if results_data.get('status') == 'OK' and results_data.get('results'):
            location = results_data['results'][0]['geometry']['location']
            lat = location['lat']
            lng = location['lng']
            print(f"[Geocoding] Success: Found Lat={lat}, Lng={lng}")
            return lat, lng
        elif results_data.get('status') == 'ZERO_RESULTS':
            print(f"[Geocoding] Error: Could not find coordinates for '{address}'. Please try a different address.")
            return None
        else:
            status = results_data.get('status')
            error_message = results_data.get('error_message', 'No error message provided.')
            print(f"[Geocoding] Error: Status '{status}'. Message: {error_message}")
            if status == 'REQUEST_DENIED':
                 print("Check if your Google Geocoding API key is correct, enabled, and has billing configured.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[Geocoding] Network or Request Error: {e}")
        return None
    except json.JSONDecodeError:
        print(f"[Geocoding] Error decoding JSON response.")
        return None
    except Exception as e:
        print(f"[Geocoding] An unexpected error occurred during geocoding: {e}")
        return None

# --- Gemini Function (Same as before) ---

def get_search_term_from_gemini(user_request: str) -> str | None:
    """Convert natural language request to contractor search term."""
    print(f"\n[Gemini] Asking Gemini for search term based on: '{user_request}'")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-1.5-flash')

        prompt = f"""
        Analyze the following user request for a home renovation or installation task.
        What is the best, concise Google Maps/Places search term (like 'electrician', 'plumber', 'handyman', 'lighting installation', 'general contractor')
        to find businesses or contractors who can perform this task?
        Output ONLY the search term(s) itself, nothing else.

        User request: "{user_request}"
        Search Term(s):"""

        response = model.generate_content(prompt)
        search_term = response.text.strip().replace('"', '').replace("'", "")

        if not search_term:
            print("[Gemini] Error: Gemini did not return a search term.")
            return None

        print(f"[Gemini] Suggested search term: '{search_term}'")
        return search_term

    except Exception as e:
        print(f"[Gemini] Error interacting with Gemini API: {e}")
        if "API key not valid" in str(e):
             print("Please check if your Gemini API key is correct and enabled.")
        return None

# --- Google Places Function (Same as before) ---

def find_contractors_google_places(search_term: str, latitude: float, longitude: float, radius: int) -> list | None:
    """Search for contractors using Google Places API."""
    print(f"\n[Places API] Searching for '{search_term}' near ({latitude}, {longitude}) within {radius} meters...")
    nearby_search_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    params = {
        'location': f"{latitude},{longitude}",
        'radius': radius,
        'keyword': search_term,
        'key': PLACES_API_KEY
    }

    try:
        response = requests.get(nearby_search_url, params=params, timeout=10)
        response.raise_for_status()
        results_data = response.json()

        if results_data.get('status') == 'OK':
            print(f"[Places API] Found {len(results_data.get('results', []))} potential results.")
            return results_data.get('results', [])
        elif results_data.get('status') == 'ZERO_RESULTS':
            print(f"[Places API] No results found for '{search_term}'.")
            return []
        else:
            status = results_data.get('status')
            error_message = results_data.get('error_message', 'No error message provided.')
            print(f"[Places API] Error: Status '{status}'. Message: {error_message}")
            if status == 'REQUEST_DENIED':
                 print("Check if your Google Places API key is correct, enabled, and has billing configured.")
            elif status == 'OVER_QUERY_LIMIT':
                 print("You may have exceeded your Google Places API quota.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[Places API] Network or Request Error: {e}")
        return None
    except json.JSONDecodeError:
        print(f"[Places API] Error decoding JSON response.")
        return None
    except Exception as e:
        print(f"[Places API] An unexpected error occurred: {e}")
        return None

# --- Main Execution ---

if __name__ == "__main__":
    # Example usage
    user_query = "I need someone to install a new chandelier in my living room."
    output_dir = Path("contractors_output")
    output_dir.mkdir(exist_ok=True)
    
    search_term = get_search_term_from_gemini(user_query)
    if not search_term:
        sys.exit(1)
        
    # For this example, we'll use a default location
    default_location = "Los Angeles, CA"
    contractors = find_contractors_google_places(
        search_term=search_term,
        latitude=34.0522,  # Los Angeles coordinates
        longitude=-118.2437,
        radius=15 * 1609  # 15 miles in meters
    )
    
    if contractors:
        # Save contractors to JSON
        with open(output_dir / "contractors.json", 'w') as f:
            json.dump(contractors, f, indent=4)

    print("\n--- Test Finished ---")
    print("🚨 REMINDER: Regenerate your API keys if you haven't already! 🚨")
    print("🚨 REMINDER: Monitor Google Cloud billing for Places & Geocoding API usage! 🚨")