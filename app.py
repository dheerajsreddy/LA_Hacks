import streamlit as st
import os
from dotenv import load_dotenv
import requests
import json
from PIL import Image
import io
import base64
import pandas as pd
from workflow_orchestrator import run_workflow
from interior_design_db import InteriorDesignDB
from pathlib import Path

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Renovation Workflow",
    page_icon="🏠",
    layout="wide"
)

# Initialize session state
if 'workflow_results' not in st.session_state:
    st.session_state.workflow_results = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'design_query_id' not in st.session_state:
    st.session_state.design_query_id = None

# Helper to save uploaded image to user_input_images/room.png
USER_IMAGE_DIR = Path(os.getenv("USER_IMAGE_DIR", "user_input_images"))
USER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
USER_IMAGE_PATH = USER_IMAGE_DIR / "room.png"

# Helper to get generated image path from DB
def get_generated_image_path(design_query_id):
    db = InteriorDesignDB()
    details = db.get_query_details(design_query_id)
    generated_images = details.get('generated_images', [])
    if generated_images:
        # generated_image_path is the 4th column (index 4)
        return generated_images[-1][4]
    return None

def display_home_depot_products(products):
    st.subheader("🏪 Home Depot Products")
    if not products:
        st.info("No products found.")
        return
    
    # Create columns for product display
    cols = st.columns(3)
    for idx, product in enumerate(products):
        with cols[idx % 3]:
            st.image(product.get('image_url', ''), use_column_width=True)
            st.write(f"**{product.get('name', 'N/A')}**")
            st.write(f"Price: ${product.get('price', 'N/A')}")
            st.write(f"Rating: {product.get('rating', 'N/A')} ⭐")
            st.write(f"[View Product]({product.get('url', '#')})")

def display_contractors(contractors):
    st.subheader("👷 Contractors")
    if not contractors:
        st.info("No contractors found.")
        return
    
    # Create a DataFrame for better display
    df = pd.DataFrame(contractors)
    st.dataframe(
        df[['name', 'address', 'rating', 'phone']],
        column_config={
            "name": "Name",
            "address": "Address",
            "rating": "Rating",
            "phone": "Phone"
        },
        hide_index=True
    )

def display_generated_image(image_data):
    st.subheader("🎨 Generated Room Design")
    if not image_data:
        st.info("No image generated yet.")
        return
    
    # Display the generated image
    st.image(image_data, use_column_width=True)

def main():
    st.title("🏠 Renovation Workflow")
    st.write("Upload a room image and describe your renovation project. We'll help you visualize your new space!")

    # User input form
    with st.form("renovation_form"):
        user_query = st.text_area(
            "Describe your renovation project",
            placeholder="e.g., I want to renovate my kitchen with modern appliances and a minimalist design..."
        )
        uploaded_image = st.file_uploader("Upload a room image", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Start Workflow")

    if submitted:
        if not user_query:
            st.error("Please describe your renovation project.")
            return
        if not uploaded_image:
            st.error("Please upload a room image.")
            return
        # Save uploaded image
        image_bytes = uploaded_image.read()
        USER_IMAGE_PATH.write_bytes(image_bytes)
        with st.spinner("Processing your request..."):
            try:
                # Run the workflow with the uploaded image
                results = run_workflow(user_query, room_image_path=USER_IMAGE_PATH)
                st.session_state.workflow_results = results
                st.session_state.current_step = 1
                st.session_state.design_query_id = results.get('design_query_id')
                st.success("Workflow completed successfully!")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                return

    # Display generated image if available
    if st.session_state.design_query_id:
        st.subheader("🎨 Generated Room Design")
        generated_image_path = get_generated_image_path(st.session_state.design_query_id)
        if generated_image_path and Path(generated_image_path).is_file():
            st.image(generated_image_path, use_column_width=True)
        else:
            st.info("No image generated yet.")

if __name__ == "__main__":
    main() 