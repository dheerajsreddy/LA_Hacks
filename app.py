import streamlit as st
import os
from pathlib import Path
from workflow_orchestrator import run_workflow
from PIL import Image
import io
import glob

# Set page config
st.set_page_config(
    page_title="Renovation Assistant",
    page_icon="🏠",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.title("🏠 Renovation Assistant")
st.markdown("""
    Upload a room image and describe your renovation needs. Our AI will help you find products and contractors!
""")

# Create two columns for the layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload Room Image")
    uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Room Image", use_column_width=True)
        
        # Save the image to the required path
        BASE_DIR = Path(r"C:\Users\meteh\OneDrive\Desktop\LA_Hacks")
        ROOM_IMAGE_PATH = BASE_DIR / "user_input_images" / "room.png"
        ROOM_IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the image
        image.save(ROOM_IMAGE_PATH)

with col2:
    st.subheader("Describe Your Needs")
    user_query = st.text_area(
        "What kind of renovation or products are you looking for?",
        placeholder="Example: I need a plush, dark grey carpet suitable for a bedroom.",
        height=150
    )

# Run button
if st.button("Start Renovation Analysis"):
    if uploaded_file is None:
        st.error("Please upload a room image first!")
    elif not user_query:
        st.error("Please describe your renovation needs!")
    else:
        with st.spinner("Analyzing your renovation needs..."):
            try:
                # Run the workflow
                run_workflow(user_query)
                st.success("Analysis complete!")
                
                # Find the most recent image in the images folder
                images_dir = BASE_DIR / "images"
                if images_dir.exists():
                    # Get all image files
                    image_files = glob.glob(str(images_dir / "*.png"))
                    if image_files:
                        # Sort by modification time (newest first)
                        latest_image = max(image_files, key=os.path.getmtime)
                        st.subheader("Generated Room Design")
                        st.image(latest_image, caption="Generated Room Design", use_column_width=True)
                    else:
                        st.warning("No generated images found in the images folder.")
                else:
                    st.warning("Images folder not found. Please check the console for results.")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ by LA Hacks Team") 