import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io
import traceback

# --- 1. Basic UI Check ---
# This will show immediately when the page loads so you know it's not blank.
st.set_page_config(page_title="Texcelle BMP Converter", layout="centered")
st.success("✅ Website is Live and Ready!")
st.title("🎨 Jacquard BMP Converter")
st.write("Convert your Sketch JPG directly into a Texcelle 8-bit BMP file.")

# --- 2. Image Processing Logic ---
def process_jacquard(input_image, width, height):
    try:
        # Load the image and convert to Grayscale
        img = Image.open(input_image).convert('L')
        
        # Resize according to user input
        img_resized = img.resize((width, height), Image.Resampling.NEAREST)
        data = np.array(img_resized)
        
        # Detect Outline (Black pencil lines become White in this mask)
        _, bw_mask = cv2.threshold(data, 120, 255, cv2.THRESH_BINARY_INV)
        
        # Find the Ground (Background) using FloodFill from corner (0,0)
        h, w = bw_mask.shape
        flood_mask = np.zeros((h+2, w+2), np.uint8)
        ground_mask = bw_mask.copy()
        cv2.floodFill(ground_mask, flood_mask, (0, 0), 255)
        
        # Find Figure (Inside areas)
        figure_mask = (ground_mask == 0)
        
        # Make the outline slightly thick (1-2 pixels)
        kernel = np.ones((2,2), np.uint8)
        outline_mask = cv2.dilate(bw_mask, kernel, iterations=1)
        
        # Create final image with 3 Colors
        final_img_data = np.zeros((h, w), dtype=np.uint8) # Default Index 0
        final_img_data[figure_mask] = 2                   # Put Index 2
        final_img_data[outline_mask > 0] = 1              # Put Index 1 over the lines
        
        # Define the exact Texcelle Palette
        palette = [
            0, 0, 255,    # Index 0: Blue (Ground)
            255, 0, 0,    # Index 1: Red (Outline)
            255, 255, 0,  # Index 2: Yellow (Figure)
        ] 
        # Add filler colors to complete the 256-color requirement
        palette += [255, 255, 255] * 253 
        
        # Generate the BMP
        output_img = Image.fromarray(final_img_data, mode='P')
        output_img.putpalette(palette)
        
        # Save to buffer
        buf = io.BytesIO()
        output_img.save(buf, format="BMP")
        return buf.getvalue()
        
    except Exception as e:
        # If any hidden error occurs in logic, it will print here
        return str(e)

# --- 3. User Input Options ---
uploaded_file = st.file_uploader("Upload your Sketch (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Sketch", use_column_width=True)
    
    # Input Boxes
    col1, col2 = st.columns(2)
    with col1:
        w = st.number_input("Width (Pixels)", min_value=10, value=512)
        r = st.number_input("Reed", min_value=1, value=100)
    with col2:
        h = st.number_input("Height (Pixels)", min_value=10, value=512)
        p = st.number_input("Pick", min_value=1, value=100)
    
    # Convert Button
    if st.button("Start Processing (Convert to BMP)"):
        with st.spinner("Processing image... Please wait..."):
            result = process_jacquard(uploaded_file, int(w), int(h))
            
            # Check if result is an error message
            if isinstance(result, str):
                st.error("❌ An error occurred during conversion:")
                st.code(result)
            else:
                st.success("✅ Conversion 100% Successful!")
                
                # Download Button
                st.download_button(
                    label="📥 Download BMP for Texcelle",
                    data=result,
                    file_name="final_jacquard.bmp",
                    mime="image/bmp"
                )
