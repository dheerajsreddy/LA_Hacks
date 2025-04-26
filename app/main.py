import json
from pathlib import Path

import click
from utils.gemini_client import diagnose, generate_step_visual
from utils.pro_finder   import choose_place_type, parse_location_string, find_nearby_pros
from utils.auto_loc     import get_location
from utils.pro_finder   import geocode        # reuse same helper

@click.command()
@click.option("--image", "-i", type=click.Path(exists=True), help="Image file")
@click.option("--video", "-v", type=click.Path(exists=True), help="Video file")
@click.option("--audio", "-a", type=click.Path(exists=True), help="Audio file")
@click.option("--desc",  "-d", help="Short text description of the problem")
@click.option("--location", "-l", help="Address or 'lat,lng' (optional)")
@click.option("--radius", "-r", default=8000, help="Search radius in metres")
def main(image=None, video=None, audio=None, desc=None, location=None, radius=8000):
    """🛠️  Multimodal Repair Assistant (Gemini + Google Maps)"""
    if not any([image, video, audio, desc]):
        click.secho("❌  Provide at least one input (image / video / audio / desc).", fg="red")
        return

    media = {}
    if image: media["image"] = Path(image)
    if video: media["video"] = Path(video)
    if audio: media["audio"] = Path(audio)

    result = diagnose(media, desc)

    click.echo("\n=== ✅ SUMMARY ===")
    click.echo(result.get("summary", "—"))

    click.echo("\n=== 🛠️  REPAIR STEPS ===")
    for i, step in enumerate(result.get("steps", []), 1):
        click.echo(f"{i}. {step}")

    click.echo("\n=== 🎨 STEP VISUALS ===")
    for i, step in enumerate(result.get("steps", []), 1):
        path = generate_step_visual(step, i)
        click.echo(f"{i}. {path or '(no image)'}")

    click.echo("\n=== 📦 METADATA ===")
    meta = {k: v for k, v in result.items() if k not in ("summary", "steps")}
    click.echo(json.dumps(meta, indent=2))

    # ---------- find a pro if needed ----------
    if result.get("needs_pro"):
        # 1. figure out (lat,lng)
        if location:
            lat, lng = (
                parse_location_string(location) if "," in location and location.count(",") == 1
                else geocode(location)
            )
            src = "CLI arg"
        else:
            got = get_location()
            if not got:
                click.secho(
                    "⚠️  Couldn’t auto-detect location – re-run with --location.", fg="yellow"
                )
                return
            lat, lng = got
            src = "IP geolocation"

        click.echo(f"\n📍 Using {src}: {lat:.4f}, {lng:.4f}")

        place_type = choose_place_type(result["summary"])
        pros = find_nearby_pros(place_type, lat, lng, radius)

        click.echo(f"\n=== 👷  {place_type.replace('_',' ').title()}s Nearby ===")
        if not pros:
            click.echo("No matching contractors found.")
        for p in pros:
            click.echo(f"• {p['name']}  ⭐ {p['rating']}  – {p['vicinity']}")
            click.echo(f"  {p['maps_url']}")

if __name__ == "__main__":
    main()
