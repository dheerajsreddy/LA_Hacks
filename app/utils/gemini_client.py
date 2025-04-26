import io
import json
import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Union

from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
assert API_KEY, "Set GOOGLE_API_KEY in your .env!"

# Configure the client
genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-1.5-flash"  # Updated to current model
# Alternatively: MODEL_NAME = "gemini-1.5-pro"

def process_image(image_path: Path) -> Dict[str, Any]:
    """Convert image to bytes with proper format handling"""
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        mime_type = "image/jpeg"
        
        return {"mime_type": mime_type, "data": buf.getvalue()}
    except Exception as e:
        raise ValueError(f"Image processing failed: {str(e)}")

def process_video(video_path: Path) -> Dict[str, Any]:
    """Process video file to bytes"""
    try:
        with open(video_path, 'rb') as f:
            video_bytes = f.read()
        
        # Get MIME type based on file extension
        mime_type, _ = mimetypes.guess_type(video_path)
        if not mime_type or not mime_type.startswith('video/'):
            mime_type = "video/mp4"  # Default to mp4 if can't determine
            
        return {"mime_type": mime_type, "data": video_bytes}
    except Exception as e:
        raise ValueError(f"Video processing failed: {str(e)}")

def process_audio(audio_path: Path) -> Dict[str, Any]:
    """Process audio file to bytes"""
    try:
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        
        # Get MIME type based on file extension
        mime_type, _ = mimetypes.guess_type(audio_path)
        if not mime_type or not mime_type.startswith('audio/'):
            mime_type = "audio/mpeg"  # Default to mp3 if can't determine
            
        return {"mime_type": mime_type, "data": audio_bytes}
    except Exception as e:
        raise ValueError(f"Audio processing failed: {str(e)}")

def diagnose(media_files: Dict[str, Path], description: str = None) -> Dict[str, Any]:
    """
    Process multiple media types and send to Gemini for diagnosis
    
    Args:
        media_files: Dictionary containing paths to media files keyed by type (image, video, audio)
        description: Optional text description of the problem
    """
    prompt = """You are Repair-GPT, a helpful assistant for diagnosing and fixing common household items.
    
For the provided media and problem description:
1. First provide a brief summary (≤30 words)
2. Then output STRICT JSON with these keys:
   - summary: string
   - steps: list of strings (repair steps)
   - needs_pro: boolean (whether professional help is needed)
   - confidence: float (0-1, your confidence in the solution)
   - parts_needed: list of strings (optional, any required parts)
   
"""
    if description:
        prompt += f"User description: {description}\n"
    
    try:
        # Build the content array for the API call
        content = [prompt]
        
        # Process and add each media file
        for media_type, file_path in media_files.items():
            if media_type == 'image':
                media_data = process_image(file_path)
            elif media_type == 'video':
                media_data = process_video(file_path)
            elif media_type == 'audio':
                media_data = process_audio(file_path)
            else:
                continue  # Skip unknown media types
                
            content.append(media_data)
        
        # Initialize the model
        model = genai.GenerativeModel(MODEL_NAME)
        
        # Make the API call
        response = model.generate_content(content)
        
        # Process the response
        raw = response.text
        json_start = raw.find("{")
        json_end = raw.rfind("}") + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in response")
            
        return json.loads(raw[json_start:json_end])
        
    except Exception as e:
        return {
            "summary": "Failed to analyze the issue",
            "steps": ["1. Please try again", "2. Contact support if problem persists"],
            "needs_pro": True,
            "confidence": 0.0,
            "error": str(e),
            "parts_needed": []
        }