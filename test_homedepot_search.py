import os
import requests
import google.generativeai as genai
import json
import sys
import re # For creating safe filenames
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

# Get API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

if not GEMINI_API_KEY or not SERPAPI_API_KEY:
    print("Error: API keys not found. Set GEMINI_API_KEY and SERPAPI_API_KEY in .env")
    sys.exit(1)

OUTPUT_DIR = "homedepot_output"
MAX_PRODUCTS_TO_PROCESS = 10 # Limit processing to manage costs/time

# --- Gemini Text Function (Same as before) ---
def get_search_query_from_gemini(user_request: str) -> str | None:
    # ... (Keep the function identical to the previous version) ...
    print(f"\n[Gemini Text] Asking Gemini for search query based on: '{user_request}'")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        prompt = f"""
        Analyze the following user request describing a home product.
        What is the best, concise search query string to use on the Home Depot website
        to find this item? Output ONLY the search query string itself, nothing else.

        User request: "{user_request}"
        Home Depot Search Query:"""
        response = model.generate_content(prompt)
        search_query = response.text.strip().replace('"', '').replace("'", "")
        if not search_query:
            print("[Gemini Text] Error: Gemini did not return a search query.")
            return None
        print(f"[Gemini Text] Suggested search query: '{search_query}'")
        return search_query
    except Exception as e:
        print(f"[Gemini Text] Error interacting with Gemini API: {e}")
        if "API key not valid" in str(e):
             print("Please check if your Gemini API key is correct and enabled.")
        return None

# --- SerpApi Home Depot Search Function (Same as before) ---
def search_home_depot_serpapi(api_key: str, query: str) -> list | None:
    # ... (Keep the function identical to the previous version) ...
    print(f"\n[SerpApi] Searching Home Depot for: '{query}'")
    params = { "engine": "home_depot", "q": query, "api_key": api_key }
    api_endpoint = "https://serpapi.com/search.json"
    try:
        response = requests.get(api_endpoint, params=params, timeout=20)
        response.raise_for_status()
        results_data = response.json()
        if "error" in results_data:
            print(f"[SerpApi] Error reported by API: {results_data['error']}")
            return None
        search_info = results_data.get("search_information", {})
        if search_info.get("organic_results_state", "") == "Fully empty":
             print(f"[SerpApi] No results found for '{query}'.")
             return []
        products = results_data.get("products")
        if products is None: products = results_data.get("organic_results")
        if products:
             print(f"[SerpApi] Found {len(products)} potential products.")
             return products
        else:
             print(f"[SerpApi] No 'products' or 'organic_results' field found.")
             return []
    except requests.exceptions.Timeout:
         print("[SerpApi] Error: Request timed out.")
         return None
    except requests.exceptions.RequestException as e:
        print(f"[SerpApi] Network or Request Error: {e}")
        return None
    except json.JSONDecodeError:
        print(f"[SerpApi] Error decoding JSON response.")
        return None
    except Exception as e:
        print(f"[SerpApi] An unexpected error occurred: {e}")
        return None

# --- Image Download Function (Same as before) ---
def download_image(url: str, save_path: str) -> bool:
    # ... (Keep the function identical to the previous version) ...
    if not url or not isinstance(url, str) or not url.startswith(('http://', 'https://')):
         print(f"[Image] Invalid or missing URL provided: '{url}'. Skipping download.")
         return False
    print(f"[Image] Attempting download: {url} -> {save_path}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, stream=True, timeout=15, headers=headers)
        response.raise_for_status()
        content_type = response.headers.get('content-type')
        if content_type and not content_type.lower().startswith('image/'):
            print(f"[Image] Warning: URL content type ({content_type}) might not be an image. Proceeding anyway.")
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(8192): f.write(chunk)
        print(f"[Image] Successfully downloaded.")
        return True
    except requests.exceptions.MissingSchema:
         print(f"[Image] Error: Invalid URL format '{url}'. Skipping.")
         return False
    except requests.exceptions.RequestException as e:
        print(f"[Image] Error downloading {url}: {e}")
        return False
    except Exception as e:
         print(f"[Image] Error saving file {save_path}: {e}")
         return False

# --- Helper to Create Safe Filenames (Same as before) ---
def create_safe_filename(text: str, suffix: str = "") -> str:
    # ... (Keep the function identical to the previous version) ...
    safe_text = re.sub(r'[<>:"/\\|?*]', '_', text)
    safe_text = re.sub(r'\s+', '_', safe_text)
    safe_text = safe_text[:100]
    return f"{safe_text}{suffix}"

# --- Main Execution ---

if __name__ == "__main__":
    # --- Example User Input ---
    user_natural_language_request = "I need a plush, dark grey carpet suitable for a bedroom."
    # user_natural_language_request = "simple white ceramic floor tile 12x12"
    # user_natural_language_request = "Lillith Navy Blue Mid Century Modern Chair" # Example from JSON
    # --- ---

    print("--- Starting Home Depot Product Search & Save Test ---")
    print(f"User Request: \"{user_natural_language_request}\"")

    # 1. Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        print(f"Creating directory: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)

    # 2. Get search query from Gemini Text
    search_query = get_search_query_from_gemini(user_natural_language_request)
    if not search_query:
        print("\n[Main] Failed to get search query from Gemini. Cannot proceed.")
        sys.exit(1)

    # 3. Search Home Depot via SerpApi
    products = search_home_depot_serpapi(SERPAPI_API_KEY, search_query)
    if products is None:
        print("\n[Main] Failed to get products from SerpApi. Cannot proceed.")
        sys.exit(1)
    if not products:
        print("\n[Main] No products found by SerpApi.")
        sys.exit(0)

    # 4. Process Products: Save Info and Download Images
    print(f"\n--- Processing up to {MAX_PRODUCTS_TO_PROCESS} Products ---")
    processed_products_info = []
    downloaded_image_count = 0

    for i, product in enumerate(products):
        if i >= MAX_PRODUCTS_TO_PROCESS:
            print(f"\n[Main] Reached processing limit ({MAX_PRODUCTS_TO_PROCESS}). Stopping.")
            break

        print(f"\n--- Product {i+1} ---")
        title = product.get('title', 'N/A')
        link = product.get('link', '#')
        price_data = product.get('price')
        rating = product.get('rating')
        reviews = product.get('reviews')
        product_id = product.get('product_id')
        seller = product.get('seller', {}).get('name', 'N/A')

        # --- CORRECTED IMAGE URL EXTRACTION ---
        image_url = None # Default to None
        thumbnails_list = product.get('thumbnails')

        if isinstance(thumbnails_list, list) and len(thumbnails_list) > 0:
             # Check if the first item is also a list (nested structure)
             inner_list = thumbnails_list[0]
             if isinstance(inner_list, list) and len(inner_list) > 0:
                  # Try to get the last URL (often highest resolution)
                  image_url = inner_list[-1]
                  print(f"[Image] Found URL in nested 'thumbnails' list: {image_url}")
             elif isinstance(thumbnails_list[0], str): # Handle case where it's just a list of strings
                  image_url = thumbnails_list[0] # Take the first one
                  print(f"[Image] Found URL directly in 'thumbnails' list: {image_url}")

        # Fallback if 'thumbnails' didn't work (keep previous logic just in case)
        if not image_url:
             image_url = product.get('thumbnail') # Singular
             if image_url: print(f"[Image] Found URL in 'thumbnail' field: {image_url}")
        if not image_url:
             image_url = product.get('image')
             if image_url: print(f"[Image] Found URL in 'image' field: {image_url}")
        # --- END OF CORRECTION ---

        print(f"Title: {title}")
        print(f"Link: {link}")
        print(f"Price: {price_data}")
        # print(f"Image URL to Download: {image_url if image_url else 'None'}") # Already printed above

        product_info = {
            "index": i + 1,
            "title": title,
            "link": link,
            "price_data": price_data,
            "rating": rating,
            "reviews": reviews,
            "product_id": product_id,
            "seller": seller,
            "found_image_url": image_url,
            "downloaded_image_path": None
        }

        if image_url:
            safe_title_part = create_safe_filename(title)
            file_ext = os.path.splitext(image_url)[1]
            # Basic check to handle potential query params in URL affecting extension
            if '?' in file_ext: file_ext = file_ext.split('?')[0]
            if not file_ext or len(file_ext) > 5 or '.' not in file_ext:
                 file_ext = ".jpg" # Default to jpg if extension looks weird/missing
            image_filename = f"product_{i+1}_{safe_title_part}{file_ext}"
            save_path = os.path.join(OUTPUT_DIR, image_filename)

            if download_image(image_url, save_path):
                product_info["downloaded_image_path"] = save_path
                downloaded_image_count += 1
        else:
             print("[Image] No valid image URL could be extracted for this product.")

        processed_products_info.append(product_info)


    # 5. Save Product Information to JSON file
    info_filename = os.path.join(OUTPUT_DIR, "product_info.json")
    print(f"\n--- Saving product information to {info_filename} ---")
    try:
        with open(info_filename, 'w') as f:
            json.dump(processed_products_info, f, indent=4)
        print("Successfully saved product info.")
    except Exception as e:
        print(f"Error saving product info JSON: {e}")

    # 6. Final Summary
    print("\n--- Final Summary ---")
    print(f"Total products found by SerpApi: {len(products)}")
    print(f"Total products processed: {len(processed_products_info)}")
    print(f"Total images successfully downloaded: {downloaded_image_count}")
    print(f"Product info saved to: {info_filename}")
    print(f"Images saved in directory: {OUTPUT_DIR}")
    print("--------------------")

    print("\n--- Test Finished ---")
    print("🚨 REMINDER: Regenerate your API keys if you haven't already! 🚨")
    print("🚨 REMINDER: Monitor SerpApi & Google Cloud billing for API usage! 🚨")