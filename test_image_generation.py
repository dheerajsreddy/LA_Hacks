import io
import os
import sys
from pathlib import Path
import PIL.Image
from dotenv import load_dotenv
import google.generativeai as genai
# No need for specific types import if not using GenerationConfig
import traceback
import mimetypes

# --- Load Environment Variables ---
print("Loading environment variables from .env file...")
load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    API_KEY = os.getenv("GEMINI_API_KEY") # Fallback

if not API_KEY:
    print("Error: GOOGLE_API_KEY (or GEMINI_API_KEY) not found...")
    sys.exit(1)
else:
    if len(API_KEY) > 8:
         print("API Key loaded successfully (masked):", API_KEY[:4] + "****" + API_KEY[-4:])
    else:
         print("API Key loaded successfully (partially masked).")


# --- File Paths (Using pathlib) ---
base_dir = Path(r"C:\Users\meteh\OneDrive\Desktop\LA_Hacks")
BASE_ROOM_IMAGE_PATH = base_dir / "user_input_images" / "room.png"
PRODUCT_IMAGE_PATH = base_dir / "homedepot_output" / "product_1_Marleen_Plush_Shag_Gray_7_ft._x_9_ft._Contemporary_Area_Rug.jpg"
OUTPUT_DIR = base_dir / "interior_design_images"
OUTPUT_FILENAME_BASE = "generated_room_apikey_exp_config" # Updated filename

# --- Instructions ---
GENERATION_PROMPT = """Using the first image (the base room) and the second image (the carpet sample), generate a new image.
The new image should show the base room, but with the entire visible floor area realistically replaced by a carpet matching the style, dark grey color, and plush texture shown in the second image (carpet sample).
Maintain the original room's perspective, lighting, and other furniture/objects."""

# --- Target Model ---
# *** Using the specific experimental model as requested ***
TARGET_MODEL_NAME = "gemini-2.0-flash-exp"
print(f"--- Using Model: {TARGET_MODEL_NAME} ---")
# !!! WARNING: Previous tests showed this model via this API did NOT generate an image !!!

# --- Helper to prepare image (returns PIL Image object) ---
def prepare_image(image_path: Path) -> PIL.Image.Image | None:
    """Loads, verifies, and converts image to RGB PIL object."""
    if not image_path.is_file():
        print(f"Error: Image file not found at '{image_path}'")
        return None
    try:
        img = PIL.Image.open(image_path)
        if img.mode != 'RGB':
            print(f"Converting image {image_path.name} from {img.mode} to RGB.")
            rgb_img = PIL.Image.new("RGB", img.size, (255, 255, 255))
            if 'A' in img.mode:
                try:
                    rgb_img.paste(img, mask=img.split()[3])
                except Exception as paste_err:
                    print(f"  Warning: Error using alpha mask for {image_path.name}: {paste_err}. Pasting directly.")
                    rgb_img.paste(img)
            else:
                rgb_img.paste(img)
            img = rgb_img
        print(f"Image loaded successfully from {image_path}")
        return img
    except Exception as e:
        print(f"Error loading or processing image {image_path}: {e}")
        traceback.print_exc()
        return None

# --- Helper function to save binary data ---
def save_binary_file(file_path: Path, data: bytes):
    """Saves binary data to a file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)
        print(f"File saved successfully to: {file_path}")
        return True
    except OSError as e:
        print(f"Error saving file {file_path}: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
         print(f"An unexpected error occurred saving file {file_path}: {e}")
         traceback.print_exc()
         return False

# --- Main Execution ---
if __name__ == "__main__":
    print("\n--- Starting Image Editing Test (Standard Gemini API - Experimental Model - With Config) ---")

    model = None
    api_response = None
    generated_image_found = False
    output_path = None
    image_saved = False

    # 1. Configure API Key and Get Model
    try:
        print(f"Configuring Gemini API key...")
        genai.configure(api_key=API_KEY)
        print("Gemini API key configured.")

        print(f"Initializing model: {TARGET_MODEL_NAME}")
        model = genai.GenerativeModel(TARGET_MODEL_NAME)
        print("Model initialized.")

    except Exception as e:
        print(f"Error configuring Gemini or initializing model: {e}")
        traceback.print_exc()
        sys.exit(1)

    # 2. Verify Input Files Exist AND Load PIL Objects
    print(f"Loading base room image: {BASE_ROOM_IMAGE_PATH}")
    room_image_pil = prepare_image(BASE_ROOM_IMAGE_PATH)
    if not room_image_pil:
        sys.exit(1)

    print(f"Loading product image: {PRODUCT_IMAGE_PATH}")
    item_image_pil = prepare_image(PRODUCT_IMAGE_PATH)
    if not item_image_pil:
        sys.exit(1)
    print("PIL image objects loaded successfully.")

    # 3. Create Output Directory
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Output directory ensured: {OUTPUT_DIR}")
    except OSError as e:
        print(f"Error creating directory '{OUTPUT_DIR}': {e}")
        sys.exit(1)

    # 4. Prepare Prompt and Call Model using initialized `model` object
    print(f"\nAttempting to generate image using model: {TARGET_MODEL_NAME}")
    print(f"Prompt: {GENERATION_PROMPT}")

    try:
        contents = [
            GENERATION_PROMPT,
            room_image_pil,
            item_image_pil
        ]

        # *** ADDING generation_config back as a dictionary ***
        # Requesting both IMAGE and TEXT based on successful editing example structure
        generation_config = {
            "response_modalities": ["IMAGE", "TEXT"]
        }
        print(f"Using Generation Config: {generation_config}")

        print("Sending request to Gemini via GenerativeModel...")
        api_response = model.generate_content(
            contents=contents,
            generation_config=generation_config, # Pass the dictionary
            stream=False
        )
        print("Received response from Gemini.")

        # 5. Process Response
        print("\n--- Processing Response Parts ---")
        if not api_response or not hasattr(api_response, 'candidates') or not api_response.candidates:
             print("Error: Response object is invalid, has no 'candidates', or it's empty.")
             if hasattr(api_response, 'prompt_feedback'):
                 print(f"Prompt Feedback (potentially blocked): {api_response.prompt_feedback}")
        else:
            candidate = api_response.candidates[0]
            finish_reason = getattr(candidate, 'finish_reason', None)
            print(f"Candidate Finish Reason: {finish_reason}")

            if finish_reason not in [1, 'STOP', 'MAX_TOKENS'] and finish_reason is not None:
                 print(f"Warning: Generation finished unexpectedly (Reason: {finish_reason}).")

            if not hasattr(candidate, 'content') or not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                 print("Error: Response candidate content or parts are missing/empty.")
            else:
                parts = candidate.content.parts
                print(f"Found {len(parts)} part(s) in candidate content.")
                for i, part in enumerate(parts):
                    print(f"--- Analyzing Part {i+1} ---")
                    if hasattr(part, "inline_data") and part.inline_data and not image_saved:
                        print("  Found 'inline_data' attribute.")
                        if hasattr(part.inline_data, "data") and isinstance(part.inline_data.data, bytes) and len(part.inline_data.data) > 0:
                            mime_type = getattr(part.inline_data, 'mime_type', 'application/octet-stream')
                            print(f"  Found image bytes data (Length: {len(part.inline_data.data)}, MIME: {mime_type})")

                            generated_image_bytes = part.inline_data.data
                            file_extension = mimetypes.guess_extension(mime_type) or ".png"
                            output_path = OUTPUT_DIR / f"{OUTPUT_FILENAME_BASE}{file_extension}"

                            print(f"  Attempting to save image to: {output_path}")
                            if save_binary_file(output_path, generated_image_bytes):
                                generated_image_found = True
                                image_saved = True
                        elif hasattr(part.inline_data, "data") and len(part.inline_data.data) == 0:
                             print("  'inline_data.data' found, but it is EMPTY (Length: 0).")
                        else:
                            print("  'inline_data' found, but 'data' attribute is missing, not bytes, or empty.")
                    elif hasattr(part, 'text') and part.text is not None:
                         text_content = part.text.strip()
                         if text_content:
                              print(f"  Text found in part: {text_content[:500]}...")
                         else:
                              print("  Text attribute found, but it is empty.")
                    else:
                        print(f"  Part type not recognized or has no usable content (Type: {type(part)}).")
                        print(f"  Part details: {part!r}")

            if hasattr(candidate, 'safety_ratings'):
                 print(f"Candidate Safety Ratings: {candidate.safety_ratings}")

        if hasattr(api_response, 'prompt_feedback'):
             print(f"Prompt Feedback: {api_response.prompt_feedback}")

    except Exception as e:
        print(f"\nAn error occurred during Gemini API call or processing: {e}")
        print("Details:")
        traceback.print_exc()
        # Check for the specific 400 error related to modalities
        if "400" in str(e) and "response modalities" in str(e).lower():
             print(f"\n*** Specific Error: Model '{TARGET_MODEL_NAME}' does not support the requested 'response_modalities' via this API. ***")
             print("   This confirms the configuration is likely incompatible.")
        else:
            print("\nOther Possible reasons listed in previous version...")


    # 6. Final Status
    print("\n--- Image Generation Test Finished ---")
    if generated_image_found and output_path:
         print(f"✅ Successfully generated and saved image to {output_path}")
    else:
         print(f"❌ Failed to generate or save image.")
         print("   - Check console output for specific errors (API key, model support, empty data, blocking).")
         print(f"   - Model '{TARGET_MODEL_NAME}' via the standard API key method seems unable to perform this task.")
         print("   - Strongly recommend trying Vertex AI with 'gemini-1.5-flash' or an Imagen model.")
    print(f"➡️ Check the '{OUTPUT_DIR}' directory and console logs.")