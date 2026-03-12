import streamlit as st
from PIL import Image, ImageEnhance
import numpy as np
import cv2
import io

# --- 1. Password Protection ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.set_page_config(page_title="Login", layout="centered")
        st.title("🔒 Login")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if password == "DHARMIK@2025":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect Password.")
        return False
    return True

# --- 2. Corrected Processing Logic ---
def process_perfect_outline(input_image, img_w, img_h, reed, pick, out_w, out_h, darkness):
    try:
        img = Image.open(input_image).convert('L')
        img_resized = img.resize((img_w, img_h), Image.Resampling.BILINEAR)
        data = np.array(img_resized)
        
        # 1. Catch lines
        _, bw_mask = cv2.threshold(data, darkness, 255, cv2.THRESH_BINARY_INV)
        
        # 2. THINNING STEP: Reset line to exactly 1 pixel thickness
        # This ensures user input matches output exactly
        kernel_thin = np.ones((3,3), np.uint8)
        bw_mask = cv2.morphologyEx(bw_mask, cv2.MORPH_OPEN, kernel_thin) # Clean noise
        
        # Using thinning algorithm to get 1-pixel skeleton
        bw_mask = cv2.ximgproc.thinning(bw_mask) 
        
        # 3. DILATION: Apply user's custom thickness
        # If user wants 2, we dilate 1-pixel line to 2
        # Kernel size must be (out_h, out_w)
        thick_kernel = np.ones((int(out_h), int(out_w)), np.uint8)
        outline_mask = cv2.dilate(bw_mask, thick_kernel, iterations=1)
        
        final_img_data = np.zeros((img_h, img_w), dtype=np.uint8)
        final_img_data[outline_mask > 0] = 1
        
        palette = [255, 255, 255, 255, 0, 0] + [255, 255, 255] * 254
        output_img = Image.fromarray(final_img_data, mode='P')
        output_img.putpalette(palette)
        
        buf = io.BytesIO()
        output_img.save(buf, format="BMP", dpi=(reed, pick))
        return buf.getvalue()
    except Exception as e:
        return str(e)

# --- 3. UI ---
if check_password():
    st.set_page_config(page_title="Jacquard BMP Converter", layout="wide")
    st.title("🎨 Jacquard BMP Pro (Exact Pixel Control)")
    
    uploaded_file = st.file_uploader("Upload Sketch", type=["jpg", "png"])
    
    if uploaded_file:
        st.subheader("⚙️ Texcelle & Outline Settings")
        c1, c2, c3 = st.columns(3)
        with c1:
            w = st.number_input("1. Width (Pixels)", value=600)
            h = st.number_input("2. Height (Pixels)", value=800)
        with c2:
            r = st.number_input("3. Reed", value=100)
            p = st.number_input("4. Pick", value=100)
        with c3:
            ow = st.number_input("5. Outline Width", value=2, min_value=1)
            oh = st.number_input("6. Outline Height", value=1, min_value=1)
            
        darkness = st.slider("Sketch Darkness", 50, 230, 150)
        
        if st.button("🚀 Generate Perfect BMP"):
            result = process_perfect_outline(uploaded_file, w, h, r, p, ow, oh, darkness)
            if isinstance(result, str): st.error(result)
            else:
                st.download_button("📥 Download BMP", result, "final_design.bmp", "image/bmp")

