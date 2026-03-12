import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io

# --- 1. Password Protection System ---
def check_password():
    """Returns True if the user enters the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.set_page_config(page_title="Login - Jacquard Converter", layout="centered")
        st.title("🔒 Secure Login")
        st.write("Please enter the password to access the converter.")
        
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if password == "DHARMIK@2025":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect Password. Please try again.")
        return False
    return True

# --- 2. Image Processing Logic ---
def process_jacquard_outline_only(input_image, img_width, img_height, out_width, out_height):
    try:
        # Load image and convert to Grayscale
        img = Image.open(input_image).convert('L')
        
        # Resize image based on user input
        img_resized = img.resize((img_width, img_height), Image.Resampling.NEAREST)
        data = np.array(img_resized)
        
        # Threshold: Identify black sketch lines (make them white in the mask)
        # Pixels darker than 120 are considered lines
        _, bw_mask = cv2.threshold(data, 120, 255, cv2.THRESH_BINARY_INV)
        
        # Set minimum outline size to 1 to avoid errors
        out_width = max(1, int(out_width))
        out_height = max(1, int(out_height))
        
        # Create kernel based on user's Outline Width and Height
        kernel = np.ones((out_height, out_width), np.uint8)
        
        # Apply Dilation (This makes the black lines thicker based on the kernel)
        outline_mask = cv2.dilate(bw_mask, kernel, iterations=1)
        
        # Create final image data array (Background = 0)
        h, w = bw_mask.shape
        final_img_data = np.zeros((h, w), dtype=np.uint8)
        
        # Set Outline pixels to Index 1
        final_img_data[outline_mask > 0] = 1
        
        # Define Texcelle Palette (Only 2 functional colors needed)
        palette = [
            255, 255, 255,  # Index 0: White (Ground)
            255, 0, 0,      # Index 1: Red (Outline)
        ]
        # Fill the rest of the 256 color palette with white
        palette += [255, 255, 255] * 254
        
        # Convert array to Image
        output_img = Image.fromarray(final_img_data, mode='P')
        output_img.putpalette(palette)
        
        # Save to buffer
        buf = io.BytesIO()
        output_img.save(buf, format="BMP")
        return buf.getvalue()
        
    except Exception as e:
        return str(e)

# --- 3. Main Application UI ---
if check_password():
    # If password is correct, show the app
    st.set_page_config(page_title="Jacquard BMP Converter", layout="wide")
    
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("🎨 Jacquard BMP Converter")
        st.write("Generate Texcelle BMP with custom Red Outline.")
    with col_logout:
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown("---")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload your Sketch (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.success("File uploaded successfully!")
        
        # Settings Layout
        st.subheader("⚙️ Image & Outline Settings")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            w = st.number_input("Image Width (Pixels)", min_value=10, value=512)
        with col2:
            h = st.number_input("Image Height (Pixels)", min_value=10, value=512)
        with col3:
            # Custom Outline Width
            out_w = st.number_input("Outline Width (Pixels)", min_value=1, value=2)
        with col4:
            # Custom Outline Height
            out_h = st.number_input("Outline Height (Pixels)", min_value=1, value=1)
            
        st.markdown("---")
        
        # Process Button
        if st.button("🚀 Generate BMP"):
            with st.spinner("Processing image..."):
                result = process_jacquard_outline_only(uploaded_file, int(w), int(h), int(out_w), int(out_h))
                
                if isinstance(result, str):
                    st.error("❌ An error occurred:")
                    st.code(result)
                else:
                    st.success("✅ BMP Generated Successfully!")
                    st.download_button(
                        label="📥 Download BMP for Texcelle",
                        data=result,
                        file_name="jacquard_outline.bmp",
                        mime="image/bmp"
                    )
