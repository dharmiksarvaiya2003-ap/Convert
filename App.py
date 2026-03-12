import streamlit as st
from PIL import Image, ImageEnhance
import numpy as np
import cv2
import io

# --- 1. Password Protection System ---
def check_password():
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

# --- NEW: Skeletonize Function (Makes lines exactly 1 pixel thin) ---
def get_skeleton(img):
    skel = np.zeros(img.shape, np.uint8)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
    temp_img = img.copy()
    while True:
        eroded = cv2.erode(temp_img, element)
        temp = cv2.dilate(eroded, element)
        temp = cv2.subtract(temp_img, temp)
        skel = cv2.bitwise_or(skel, temp)
        temp_img = eroded.copy()
        if cv2.countNonZero(temp_img) == 0:
            break
    return skel

# --- 2. Advanced Image Processing Logic ---
def process_jacquard_outline_only(input_image, img_w, img_h, reed, pick, out_w, out_h, darkness_threshold):
    try:
        # Load image and convert to Grayscale
        img = Image.open(input_image).convert('L')
        
        # Enhance Contrast so faint pencil lines become darker
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # Resize based on 1. Width (Pixels) and 2. Height (Pixels) using BILINEAR for smooth curves
        img_resized = img.resize((img_w, img_h), Image.Resampling.BILINEAR)
        data = np.array(img_resized)
        
        # Threshold: Identify black sketch lines
        _, bw_mask = cv2.threshold(data, darkness_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # --- STEP 1: Close Gaps (Prevents broken lines on curves) ---
        close_kernel = np.ones((2, 2), np.uint8)
        bw_mask = cv2.morphologyEx(bw_mask, cv2.MORPH_CLOSE, close_kernel)
        
        # --- STEP 2: Make lines EXACTLY 1 pixel thin (Removes double thickness) ---
        skel_mask = get_skeleton(bw_mask)
        
        # --- STEP 3: Apply Custom Outline Thickness cleanly ---
        out_w = max(1, int(out_w))
        out_h = max(1, int(out_h))
        thick_kernel = np.ones((out_h, out_w), np.uint8)
        outline_mask = cv2.dilate(skel_mask, thick_kernel, iterations=1)
        
        # Create final image data array (Background = 0)
        final_img_data = np.zeros((img_h, img_w), dtype=np.uint8)
        
        # Set Outline pixels to Index 1 (Red)
        final_img_data[outline_mask > 0] = 1
        
        # Define Texcelle Palette: 0 = White (Ground), 1 = Red (Outline)
        palette = [
            255, 255, 255,  # Index 0: White
            255, 0, 0,      # Index 1: Red
        ]
        palette += [255, 255, 255] * 254 # Fill the rest
        
        # Convert array to Image
        output_img = Image.fromarray(final_img_data, mode='P')
        output_img.putpalette(palette)
        
        # Save to buffer
        buf = io.BytesIO()
        # Pass Reed and Pick into the DPI header for Texcelle Paper Format
        output_img.save(buf, format="BMP", dpi=(reed, pick))
        return buf.getvalue()
        
    except Exception as e:
        return str(e)

# --- 3. Main Application UI ---
if check_password():
    st.set_page_config(page_title="Jacquard BMP Converter", layout="wide")
    
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("🎨 Jacquard BMP Converter (Pro)")
        st.write("Texcelle 'Paper Format' Compatible Outline Generator (Pixel Perfect Mode)")
    with col_logout:
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload your Sketch (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.subheader("⚙️ Texcelle Format Settings")
        
        # 6 Options layout as requested
        col1, col2, col3 = st.columns(3)
        with col1:
            w = st.number_input("1. Width (Pixels)", min_value=10, value=600)
            h = st.number_input("2. Height (Pixels)", min_value=10, value=800)
        with col2:
            r = st.number_input("3. Reed", min_value=1, value=100)
            p = st.number_input("4. Pick", min_value=1, value=100)
        with col3:
            out_w = st.number_input("5. Outline Width", min_value=1, value=2)
            out_h = st.number_input("6. Outline Height", min_value=1, value=1)
            
        st.markdown("---")
        st.subheader("🎛️ Curve Smoothing & Line Catcher")
        st.write("જો લાઈનો વચ્ચેથી તૂટેલી આવે, તો નીચેનું સ્લાઈડર થોડું વધારીને ફરી ટ્રાય કરો (જેથી આછી પેન્સિલ પણ પકડાઈ જાય).")
        darkness = st.slider("Sketch Darkness Threshold", min_value=50, max_value=230, value=150, step=10)
            
        st.markdown("---")
        
        if st.button("🚀 Generate Perfect BMP"):
            with st.spinner("Processing 1-pixel exact continuous lines for Texcelle..."):
                result = process_jacquard_outline_only(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(darkness)
                )
                
                if isinstance(result, str):
                    st.error("❌ An error occurred:")
                    st.code(result)
                else:
                    st.success("✅ BMP Generated Successfully! Lines are EXACTLY the width & height you specified.")
                    st.download_button(
                        label="📥 Download BMP for Texcelle",
                        data=result,
                        file_name="jacquard_texcelle_format.bmp",
                        mime="image/bmp"
              )
