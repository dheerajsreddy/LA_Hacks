import json
from pathlib import Path
import time

import click
from utils.gemini_client import diagnose, generate_step_visual
from utils.pro_finder   import choose_place_type, parse_location_string, find_nearby_pros
from utils.auto_loc     import get_location
from utils.pro_finder   import geocode
from utils.product_finder import search_products

@click.command()
@click.option("--image", "-i", type=click.Path(exists=True), help="Image file")
@click.option("--video", "-v", type=click.Path(exists=True), help="Video file")
@click.option("--audio", "-a", type=click.Path(exists=True), help="Audio file")
@click.option("--desc",  "-d", help="Short text description of the problem")
@click.option("--location", "-l", help="Address or 'lat,lng' (optional)")
@click.option("--radius", "-r", default=8000, help="Search radius in metres")
def main(image=None, video=None, audio=None, desc=None, location=None, radius=8000):
    if not any([image, video, audio, desc]):
        print(json.dumps({
            "summary": [],
            "repair_steps": [],
            "step_visuals": [],
            "metadata": {},
            "contractors_nearby": [],
            "products_needed": []
        }))
        return

    media = {}
    if image: media["image"] = Path(image)
    if video: media["video"] = Path(video)
    if audio: media["audio"] = Path(audio)

    result = diagnose(media, desc)

    # Retry once if failed
    if result.get("summary", "") == "Failed to analyse the issue.":
        time.sleep(1)  # small wait for stability
        result = diagnose(media, desc)

    summary = result.get("summary", "")
    steps = result.get("steps", [])
    metadata = {k: v for k, v in result.items() if k not in ("summary", "steps")}

    visuals = []
    if steps:
        for idx, step in enumerate(steps, 1):
            try:
                path = generate_step_visual(step, idx)
                visuals.append(path if path else "")
            except Exception:
                visuals.append("")

    contractors = []
    lat, lng = None, None
    if result.get("needs_pro"):
        if location:
            lat, lng = (
                parse_location_string(location) if "," in location and location.count(",") == 1
                else geocode(location)
            )
        else:
            got = get_location()
            if got:
                lat, lng = got
        if lat is not None and lng is not None:
            place_type = choose_place_type(result.get("summary", ""))
            found_pros = find_nearby_pros(place_type, lat, lng, radius)
            contractors = [
                {
                    "name": p.get("name", ""),
                    "rating": p.get("rating", ""),
                    "address": p.get("vicinity", ""),
                    "distance_km": p.get("distance_km", ""),
                    "maps_url": p.get("maps_url", "")
                }
                for p in found_pros
            ]

    products = []
    if result.get("parts_needed") and lat is not None and lng is not None:
        for part in result["parts_needed"]:
            found_products = search_products(part, lat, lng)
            for p in found_products:
                products.append({
                    "product_name": part,
                    "title": p.get("title", ""),
                    "price": p.get("price", ""),
                    "rating": p.get("rating", ""),
                    "store": p.get("store", ""),
                    "distance_km": p.get("distance_km", ""),
                    "link": p.get("link", "")
                })

    output = {
        "summary": [summary] if summary else [],
        "repair_steps": steps if steps else [],
        "step_visuals": visuals if visuals else [],
        "metadata": metadata if metadata else {},
        "contractors_nearby": contractors if contractors else [],
        "products_needed": products if products else []
    }

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
