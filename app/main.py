import json
from pathlib import Path

import click
from utils.gemini_client import diagnose, generate_step_visual

@click.command()
@click.option("--image", "-i", type=click.Path(exists=True), help="Path to an image file (jpg/png/webp/...)")
@click.option("--video", "-v", type=click.Path(exists=True), help="Path to a video file (mp4/mov/webm/...)")
@click.option("--audio", "-a", type=click.Path(exists=True), help="Path to an audio file (mp3/wav/ogg/...)")
@click.option("--desc", "-d", help="Short plain-text description of the problem")
def main(image: str = None, video: str = None, audio: str = None, desc: str = None):
    """🛠️ Multimodal Repair Assistant powered by Gemini 2.5 Flash + 2.0 Flash Image Gen."""

    if not any([image, video, audio, desc]):
        click.secho("❌ Error: Provide at least one input (image, video, audio, or description).", fg="red")
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
    print(result.get("summary", "No summary available"))

    print("\n=== 🛠️ REPAIR STEPS ===")
    steps = result.get("steps", [])
    if steps:
        for idx, step in enumerate(steps, 1):
            print(f"{idx}. {step}")
    else:
        print("No repair steps provided.")

    print("\n=== 🎨 STEP VISUALS ===")
    if steps:
        for idx, step in enumerate(steps, 1):
            try:
                image_path = generate_step_visual(step, idx)
                if image_path:
                    print(f"{idx}. Visual Illustration saved at: {image_path}")
                else:
                    print(f"{idx}. (No visual generated for this step.)")
            except Exception as e:
                print(f"{idx}. (Failed to generate visual: {e})")
    else:
        print("No steps available for visualization.")

    print("\n=== 📦 METADATA ===")
    metadata = {k: v for k, v in result.items() if k not in ("summary", "steps")}
    print(json.dumps(metadata, indent=2))

if __name__ == "__main__":
    main()
