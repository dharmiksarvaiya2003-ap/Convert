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

# --- 2. Advanced Image Processing Logic ---
def process_jacquard_outline_only(input_image, reed, pick, out_width, out_height, darkness_threshold):
    try:
        # Load image and convert to Grayscale
        img = Image.open(input_image).convert('L')
        
        # Enhance Contrast so faint pencil lines become darker
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # Resize using BILINEAR (Preserves lines much better than NEAREST)
        img_resized = img.resize((reed, pick), Image.Resampling.BILINEAR)
        data = np.array(img_resized)
        
        # Threshold: Identify black sketch lines
        # Higher threshold = catches lighter lines. Lower threshold = only catches very dark lines.
        _, bw_mask = cv2.threshold(data, darkness_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # --- MAGIC STEP: Close Gaps (Prevents broken lines) ---
        # This connects pixels that are very close to each other
        close_kernel = np.ones((2, 2), np.uint8)
        bw_mask = cv2.morphologyEx(bw_mask, cv2.MORPH_CLOSE, close_kernel)
        
        # Apply Custom Outline Thickness (Dilation)
        out_width = max(1, int(out_width))
        out_height = max(1, int(out_height))
        thick_kernel = np.ones((out_height, out_width), np.uint8)
        outline_mask = cv2.dilate(bw_mask, thick_kernel, iterations=1)
        
        # Create final image data array (Background = 0)
        h, w = outline_mask.shape
        final_img_data = np.zeros((h, w), dtype=np.uint8)
        
        # Set Outline pixels to Index 1
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
        output_img.save(buf, format="BMP")
        return buf.getvalue()
        
    except Exception as e:
        return str(e)

# --- 3. Main Application UI ---
if check_password():
    st.set_page_config(page_title="Jacquard BMP Converter", layout="wide")
    
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("🎨 Jacquard BMP Converter (Pro)")
        st.write("Generate smooth, continuous Texcelle BMP with custom Red Outline.")
    with col_logout:
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload your Sketch (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.subheader("⚙️ Jacquard Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            reed = st.number_input("Reed (Width)", min_value=10, value=600)
            out_w = st.number_input("Outline Width (Thickness)", min_value=1, value=2)
        with col2:
            pick = st.number_input("Pick (Height)", min_value=10, value=800)
            out_h = st.number_input("Outline Height (Thickness)", min_value=1, value=2)
            
        st.markdown("---")
        st.subheader("🎛️ Advanced Line Tuning")
        st.write("જો લાઈનો તૂટેલી આવે (Broken lines), તો નીચેનું સ્લાઈડર જમણી બાજુ (વધારે) સેટ કરો.")
        darkness = st.slider("Sketch Darkness Catcher", min_value=50, max_value=230, value=150, step=10)
            
        st.markdown("---")
        
        if st.button("🚀 Generate Perfect BMP"):
            with st.spinner("Smoothing curves and processing image..."):
                result = process_jacquard_outline_only(uploaded_file, int(reed), int(pick), int(out_w), int(out_h), int(darkness))
                
                if isinstance(result, str):
                    st.error("❌ An error occurred:")
                    st.code(result)
                else:
                    st.success("✅ BMP Generated Successfully with Smooth Curves!")
                    st.download_button(
                        label="📥 Download BMP for Texcelle",
                        data=result,
                        file_name="jacquard_outline_perfect.bmp",
                        mime="image/bmp"
                    )
