import json
from pathlib import Path

import click
from utils.gemini_client import diagnose


@click.command()
@click.option("--image", "-i", type=click.Path(exists=True), help="Path to image file")
@click.option("--video", "-v", type=click.Path(exists=True), help="Path to video file")
@click.option("--audio", "-a", type=click.Path(exists=True), help="Path to audio file")
@click.option("--desc", "-d", help="Short plain-text description of the problem")
def main(image: str = None, video: str = None, audio: str = None, desc: str = None):
    """Multimodal diagnosis using Gemini – supports image, video, audio, and text."""
    if not any([image, video, audio, desc]):
        click.echo("❌ Error: At least one input (image, video, audio, or text) is required.")
        return

    media_files = {}
    if image:
        media_files['image'] = Path(image)
    if video:
        media_files['video'] = Path(video)
    if audio:
        media_files['audio'] = Path(audio)

    result = diagnose(media_files, desc)

    print("\n=== ✅ SUMMARY ===")
    print(result["summary"])

    print("\n=== 🛠️ REPAIR STEPS ===")
    for idx, step in enumerate(result["steps"], 1):
        print(f"{idx}. {step}")

    print("\n=== 📦 METADATA ===")
    print(json.dumps(
        {k: v for k, v in result.items() if k not in ("summary", "steps")},
        indent=2
    ))


if __name__ == "__main__":
    main()
