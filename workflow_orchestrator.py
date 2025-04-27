import os
import json
from pathlib import Path
from test_homedepot_search import get_search_query_from_gemini, search_home_depot_serpapi, download_product_images
from test_contractor_search_dynamic_location import get_search_term_from_gemini, find_contractors_google_places
from test_image_generation import generate_room_image, generate_image_prompt
from home_depot_db import HomeDepotDB
from contractors_db import ContractorsDB
from interior_design_db import InteriorDesignDB
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = Path(r"C:\Users\meteh\OneDrive\Desktop\LA_Hacks")
ROOM_IMAGE_PATH = BASE_DIR / "user_input_images" / "room.png"
IMAGES_DIR = BASE_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Initialize databases
db_hd = HomeDepotDB()
db_contractors = ContractorsDB()
db_design = InteriorDesignDB()

def run_workflow(user_query: str, room_image_path: Path = ROOM_IMAGE_PATH):
    """
    Orchestrates the workflow between the three agents.
    """
    print("\n=== Starting Workflow ===")
    print(f"User Query: {user_query}")
    print(f"Room Image: {room_image_path}")

    # Save initial query to Home Depot DB
    hd_query_id = db_hd.save_user_query(user_query, str(room_image_path))

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

    # Download product images to images/ and update product dicts
    downloaded_images = download_product_images(products, IMAGES_DIR)
    for i, img_path in enumerate(downloaded_images):
        products[i]["downloaded_image_path"] = str(img_path)

    # Save products to Home Depot DB
    db_hd.save_products(hd_query_id, products)

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

    # Save query and contractors to Contractors DB
    contractors_query_id = db_contractors.save_user_query(user_query, default_location)
    if contractors:
        db_contractors.save_contractors(contractors_query_id, contractors)

    # Agent 3: Image Generation
    print("\n=== Agent 3: Generating Room Image ===")
    # Use the first downloaded product image
    product_image_path = downloaded_images[0]
    print(f"Using product image: {product_image_path}")

    # Save query to Interior Design DB
    design_query_id = db_design.save_user_query(user_query, str(room_image_path))

    # Generate the image prompt
    image_prompt = generate_image_prompt(user_query)
    if not image_prompt:
        print("Failed to generate image prompt. Exiting workflow.")
        return

    # Generate the combined image
    generated_image_path = IMAGES_DIR / f"generated_{design_query_id}.png"
    success = generate_room_image(room_image_path, product_image_path, user_query, generated_image_path)
    
    if success:
        print(f"Successfully generated image at {generated_image_path}")
        db_design.save_generated_image(
            query_id=design_query_id,
            room_image_path=str(room_image_path),
            product_image_path=str(product_image_path),
            generated_image_path=str(generated_image_path),
            generation_prompt=image_prompt
        )
    else:
        print("Failed to generate image")

    print("\n=== Workflow Completed ===")
    return {
        "home_depot_query_id": hd_query_id,
        "contractors_query_id": contractors_query_id,
        "design_query_id": design_query_id
    }

if __name__ == "__main__":
    # Example usage
    user_query = "I need a plush, dark grey carpet suitable for a bedroom."
    ids = run_workflow(user_query)
    print("\nQuery IDs:", ids)
    
    # Print Home Depot history
    print("\n=== Home Depot Query History ===")
    hd_history = db_hd.get_query_history(limit=5)
    for query in hd_history:
        print(f"Query ID: {query[0]}")
        print(f"Query: {query[1]}")
        print(f"Timestamp: {query[2]}")
        print(f"Products: {query[3]}")
        print("---")

    # Print Contractors history
    print("\n=== Contractors Query History ===")
    contractor_history = db_contractors.get_query_history(limit=5)
    for query in contractor_history:
        print(f"Query ID: {query[0]}")
        print(f"Query: {query[1]}")
        print(f"Timestamp: {query[2]}")
        print(f"Contractors: {query[3]}")
        print("---")

    # Print Interior Design Images history
    print("\n=== Interior Design Query History ===")
    design_history = db_design.get_query_history(limit=5)
    for query in design_history:
        print(f"Query ID: {query[0]}")
        print(f"Query: {query[1]}")
        print(f"Timestamp: {query[2]}")
        print(f"Generated Images: {query[3]}")
        print("---") 