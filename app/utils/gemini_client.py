import io
import os
import json
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
from google.generativeai import types

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
assert API_KEY, "Set GOOGLE_API_KEY in your .env!"

# Configure the client
genai.configure(api_key=API_KEY)

# Models
DIAGNOSIS_MODEL = "gemini-2.5-flash-preview-04-17"
IMAGE_MODEL = "gemini-2.0-flash-exp-image-generation"

diagnosis_model = genai.GenerativeModel(DIAGNOSIS_MODEL)
image_model = genai.GenerativeModel(IMAGE_MODEL)

def process_image(image_path: Path) -> Dict[str, Any]:
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return {"mime_type": "image/jpeg", "data": buf.getvalue()}

def process_video(video_path: Path) -> Dict[str, Any]:
    with open(video_path, "rb") as f:
        return {"mime_type": "video/mp4", "data": f.read()}

def process_audio(audio_path: Path) -> Dict[str, Any]:
    with open(audio_path, "rb") as f:
        return {"mime_type": "audio/mpeg", "data": f.read()}

def diagnose(media_files: Dict[str, Path], description: str = None) -> Dict[str, Any]:
    """
    Diagnose an issue using Gemini 2.5 Pro with multimodal input (text, image, audio, video).
    """
    prompt = """You are Repair-GPT, a helpful assistant for diagnosing and fixing household items.

1. Provide a short summary (≤30 words).
2. Then output STRICT JSON:
- summary: string
- steps: list of strings
- needs_pro: boolean
- confidence: float (0-1)
- parts_needed: list of strings (optional)

"""
    if description:
        prompt += f"User description: {description}\n"

    content = [prompt]

    for media_type, file_path in media_files.items():
        if media_type == "image":
            content.append(process_image(file_path))
        elif media_type == "video":
            content.append(process_video(file_path))
        elif media_type == "audio":
            content.append(process_audio(file_path))

    try:
        response = diagnosis_model.generate_content(content)
        raw = response.text
        json_start = raw.find("{")
        json_end = raw.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in response.")

        return json.loads(raw[json_start:json_end])

    except Exception as e:
        return {
            "summary": "Failed to analyze the issue",
            "steps": ["1. Please try again", "2. Contact support if needed"],
            "needs_pro": True,
            "confidence": 0.0,
            "error": str(e),
            "parts_needed": []
        }

def generate_step_visual(step_description: str, idx: int) -> str:
    """
    Generate a simple instructional image for the given repair step using Gemini 2.0 Flash.
    """
    try:
        response = image_model.generate_content(
        contents=f"Create a simple hand-drawn instructional sketch for this repair step: {step_description}",
        generation_config={
        "response_modalities": ["TEXT", "IMAGE"]
    })

        parts = response.candidates[0].content.parts

        for part in parts:
            if hasattr(part, "inline_data") and part.inline_data is not None:
                img = Image.open(io.BytesIO(part.inline_data.data))
                os.makedirs("outputs", exist_ok=True)
                save_path = f"outputs/step_{idx}.png"
                img.save(save_path)
                return save_path

        return None

    except Exception as e:
        print(f"Image generation failed for step {idx}: {e}")
        return None
