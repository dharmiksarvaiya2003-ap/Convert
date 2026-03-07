import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io

def process_jacquard(input_image, width, height, reed, pick):
    # 1. Image Load & Grayscale
    img = Image.open(input_image).convert('L')
    
    # 2. Resize
    img_resized = img.resize((width, height), Image.Resampling.NEAREST)
    data = np.array(img_resized)
    
    # 3. Create Masks
    # Sketch lines are usually dark (thresholding)
    _, bw_mask = cv2.threshold(data, 127, 255, cv2.THRESH_BINARY_INV)
    
    # 4. Flood fill to find background (Ground)
    h, w = bw_mask.shape
    flood_mask = np.zeros((h+2, w+2), np.uint8)
    ground_mask = bw_mask.copy()
    cv2.floodFill(ground_mask, flood_mask, (0, 0), 255)
    
    # Figure is what's not ground
    figure_mask = (ground_mask == 0)
    
    # 5. Outline (Red) - dilate the edges a bit
    kernel = np.ones((2,2), np.uint8)
    outline_mask = cv2.dilate(bw_mask, kernel, iterations=1)
    
    # 6. Create Final Indexed Image (8-bit)
    # 0: Blue (Ground), 1: Red (Outline), 2: Yellow (Figure)
    final_img_data = np.zeros((h, w), dtype=np.uint8)
    final_img_data[figure_mask] = 2
    final_img_data[outline_mask > 0] = 1
    
    # Define Palette (RGB)
    palette = [
        0, 0, 255,    # 0: Blue
        255, 0, 0,    # 1: Red
        255, 255, 0,  # 2: Yellow
    ] + [255, 255, 255] * 253 # Fill remaining colors
    
    output_img = Image.fromarray(final_img_data, mode='P')
    output_img.putpalette(palette)
    
    # Save to Buffer
    buf = io.BytesIO()
    output_img.save(buf, format="BMP")
    return buf.getvalue()

# --- STREAMLIT UI ---
st.set_page_config(page_title="Jacquard BMP Converter", layout="centered")

st.title("🎨 Jacquard BMP Converter")
st.subheader("Texcelle Compatible File Generator")

uploaded_file = st.file_uploader("Upload Sketch (JPG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        w = st.number_input("Width (Pixels)", value=512)
        r = st.number_input("Reed", value=100)
    with col2:
        h = st.number_input("Height (Pixels)", value=512)
        p = st.number_input("Pick", value=100)
    
    if st.button("Convert to BMP"):
        with st.spinner("Processing..."):
            try:
                result = process_jacquard(uploaded_file, w, h, r, p)
                st.success("Conversion Complete!")
                st.download_button(
                    label="📥 Download BMP for Texcelle",
                    data=result,
                    file_name="jacquard_design.bmp",
                    mime="image/bmp"
                )
            except Exception as e:
                st.error(f"Error: {e}")
else:
    st.info("Please upload a JPG file to start.")

