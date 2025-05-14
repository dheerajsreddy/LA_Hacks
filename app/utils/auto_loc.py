"""
IP-based geolocation for CLI use.
"""
import os, requests
from typing import Optional, Tuple

def get_location() -> Optional[Tuple[float, float]]:
    override = os.getenv("LOCATION_OVERRIDE")
    if override:
        try:
            return tuple(map(float, override.split(",")))
        except ValueError:
            pass

    try:
        r = requests.get("http://ip-api.com/json", timeout=3).json()
        if r.get("status") == "success":
            return r["lat"], r["lon"]
    except requests.RequestException:
        pass
    return None