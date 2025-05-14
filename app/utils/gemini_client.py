import io, os, json
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
assert API_KEY, "Set GOOGLE_API_KEY in .env"

genai.configure(api_key=API_KEY)

DIAGNOSIS_MODEL = "gemini-2.5-flash-preview-04-17"
IMAGE_MODEL     = "gemini-2.0-flash-exp-image-generation"

diagnosis_model = genai.GenerativeModel(DIAGNOSIS_MODEL)
image_model     = genai.GenerativeModel(IMAGE_MODEL)


# ---------- helpers to stream media into Gemini ----------

def _image_part(path: Path):
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO(); img.save(buf, "JPEG")
    return {"mime_type": "image/jpeg", "data": buf.getvalue()}

def _video_part(path: Path):
    return {"mime_type": "video/mp4", "data": path.read_bytes()}

def _audio_part(path: Path):
    return {"mime_type": "audio/mpeg", "data": path.read_bytes()}


# ---------- public API ----------

def diagnose(media: Dict[str, Path], desc: str | None) -> Dict[str, Any]:
    """
    Feed image / video / audio / text to Gemini and
    return strict-JSON diagnosis.
    """
    prompt = (
        "You are Repair-GPT, a helpful assistant for diagnosing and fixing "
        "household items.\n\n"
        "1. Provide a ≤30-word summary.\n"
        "2. Then output STRICT JSON with keys:\n"
        "   summary, steps, needs_pro, confidence, parts_needed (list)\n"
    )
    if desc:
        prompt += f"\nUser description: {desc}\n"

    content = [prompt]
    for kind, path in media.items():
        content.append(
            _image_part(path)  if kind == "image" else
            _video_part(path)  if kind == "video" else
            _audio_part(path)  if kind == "audio" else
            None
        )

    try:
        raw = diagnosis_model.generate_content(content).text
        j = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
        return j
    except Exception as e:
        return {
            "summary": "Failed to analyse the issue.",
            "steps": ["Try again later.", "Contact support."],
            "needs_pro": True,
            "confidence": 0.0,
            "error": str(e),
            "parts_needed": [],
        }


def generate_step_visual(step: str, idx: int) -> str | None:
    """
    Create a sketch-style illustration for one repair step.
    Returns the PNG path or None.
    """
    try:
        rsp   = image_model.generate_content(
            contents = f"Create a simple hand-drawn instructional sketch for: {step}",
            generation_config = {"response_modalities": ["TEXT", "IMAGE"]},
        )
        for p in rsp.candidates[0].content.parts:
            if getattr(p, "inline_data", None):
                data = p.inline_data.data
                img_path = Path("outputs"); img_path.mkdir(exist_ok=True)
                out = img_path / f"step_{idx}.png"
                Image.open(io.BytesIO(data)).save(out)
                return str(out)
    except Exception:
        pass
    return None