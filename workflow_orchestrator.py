import os
import json
from pathlib import Path
from test_homedepot_search import get_search_query_from_gemini, search_home_depot_serpapi, download_product_images
from test_contractor_search_dynamic_location import get_search_term_from_gemini, find_contractors_google_places
from test_image_generation import generate_room_image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = Path(r"C:\Users\meteh\OneDrive\Desktop\LA_Hacks")
ROOM_IMAGE_PATH = BASE_DIR / "user_input_images" / "room.png"
HOMEDEPOT_OUTPUT_DIR = BASE_DIR / "homedepot_output_test"
CONTRACTORS_OUTPUT_DIR = BASE_DIR / "contractors_output"
INTERIOR_DESIGN_OUTPUT_DIR = BASE_DIR / "interior_design_images"

# Create output directories
HOMEDEPOT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CONTRACTORS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INTERIOR_DESIGN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run_workflow(user_query: str, room_image_path: Path = ROOM_IMAGE_PATH):
    """
    Orchestrates the workflow between the three agents.
    """
    print("\n=== Starting Workflow ===")
    print(f"User Query: {user_query}")
    print(f"Room Image: {room_image_path}")

    # Agent 1: Home Depot Search
    print("\n=== Agent 1: Searching Home Depot ===")
    search_query = get_search_query_from_gemini(user_query)
    if not search_query:
        print("Failed to generate search query. Exiting workflow.")
        return

    products = search_home_depot_serpapi(os.getenv("SERPAPI_API_KEY"), search_query)
    if not products:
        print("No products found. Exiting workflow.")
        return

    # Save products to JSON
    products_file = HOMEDEPOT_OUTPUT_DIR / "products.json"
    with open(products_file, 'w') as f:
        json.dump(products, f, indent=4)
    print(f"Products saved to {products_file}")

    # Download product images
    print("\nDownloading product images...")
    downloaded_images = download_product_images(products, HOMEDEPOT_OUTPUT_DIR)
    if not downloaded_images:
        print("No product images were downloaded. Exiting workflow.")
        return

    # Agent 2: Contractor Search
    print("\n=== Agent 2: Searching Contractors ===")
    contractor_query = get_search_term_from_gemini(user_query)
    if not contractor_query:
        print("Failed to generate contractor search term. Exiting workflow.")
        return

    # For this example, we'll use a default location
    default_location = "Los Angeles, CA"
    contractors = find_contractors_google_places(
        search_term=contractor_query,
        latitude=34.0522,  # Los Angeles coordinates
        longitude=-118.2437,
        radius=15 * 1609  # 15 miles in meters
    )

    if contractors:
        # Save contractors to JSON
        contractors_file = CONTRACTORS_OUTPUT_DIR / "contractors.json"
        with open(contractors_file, 'w') as f:
            json.dump(contractors, f, indent=4)
        print(f"Contractors saved to {contractors_file}")

    # Agent 3: Image Generation
    print("\n=== Agent 3: Generating Room Image ===")
    # Use the first downloaded product image
    product_image_path = downloaded_images[0]
    print(f"Using product image: {product_image_path}")

    # Generate the combined image
    output_path = INTERIOR_DESIGN_OUTPUT_DIR / "generated_room.png"
    success = generate_room_image(room_image_path, product_image_path, user_query, output_path)
    
    if success:
        print(f"Successfully generated image at {output_path}")
    else:
        print("Failed to generate image")

    print("\n=== Workflow Completed ===")

if __name__ == "__main__":
    # Example usage
    user_query = "I want to get a new blue comforter for my bed in my bedroom."
    run_workflow(user_query) 