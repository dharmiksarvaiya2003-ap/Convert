import streamlit as st
from PIL import Image
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

# --- 2. Advanced Image Processing: Continuous & Smooth Curves ---
def process_jacquard_perfect_curves(input_image, img_w, img_h, reed, pick, out_w, out_h, darkness_threshold):
    try:
        # 1. Load image and convert to standard RGB/Grayscale
        img_pil = Image.open(input_image).convert('RGB')
        img_cv = np.array(img_pil)
        img_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        
        # 2. Resize directly to the target jacquard dimensions 
        # INTER_LANCZOS4 is crucial here because it prevents blocky jagged edges during resizing
        resized = cv2.resize(img_gray, (img_w, img_h), interpolation=cv2.INTER_LANCZOS4)
        
        # 3. Blur the image smoothly before finding lines 
        # This blends the tiny breaks in pencil marks into a single solid path
        blurred = cv2.GaussianBlur(resized, (5, 5), 0)
        
        # 4. Thresholding: Separate the sketch from the background
        _, binary = cv2.threshold(blurred, darkness_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # 5. Gap Closing (Healing) 
        # Connects any remaining missing pixels so lines NEVER break
        heal_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed_mask = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, heal_kernel)
        
        # 6. Perfect Thinning (Guo-Hall Algorithm)
        # It creates a mathematically perfect 1-pixel centerline of the curves without zigzagging
        skeleton = cv2.ximgproc.thinning(closed_mask, thinningType=cv2.ximgproc.THINNING_GUOHALL)
        
        # 7. Apply Exact Outline Thickness (Out_W and Out_H)
        out_w = max(1, int(out_w))
        out_h = max(1, int(out_h))
        
        # Use an Elliptical brush for dilation to keep curved corners perfectly round
        if out_w <= 2 and out_h <= 2:
            brush = cv2.getStructuringElement(cv2.MORPH_RECT, (out_w, out_h))
        else:
            brush = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (out_w, out_h))
            
        final_mask = cv2.dilate(skeleton, brush, iterations=1)
        
        # 8. Create Final Array and Map to Jacquard Palette
        # Background = 0, Sketch Lines = 1
        final_img_data = np.zeros((img_h, img_w), dtype=np.uint8)
        final_img_data[final_mask > 0] = 1
        
        # Palette: Index 0 is White, Index 1 is Red
        palette = [
            255, 255, 255,  # 0: White Ground
            255, 0, 0,      # 1: Red Outline
        ]
        palette += [255, 255, 255] * 254 # Fill the remaining 254 colors with white
        
        output_img = Image.fromarray(final_img_data, mode='P')
        output_img.putpalette(palette)
        
        # Save exact DPI for Texcelle
        buf = io.BytesIO()
        output_img.save(buf, format="BMP", dpi=(reed, pick))
        return buf.getvalue()
        
    except Exception as e:
        return str(e)

# --- 3. Main Application UI ---
if check_password():
    st.set_page_config(page_title="Jacquard BMP Pro", layout="wide")
    
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("🎨 Jacquard BMP Converter (Pro)")
        st.write("High-Quality Continuous Curves & Exact Thickness Generator")
    with col_logout:
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload your Sketch (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.subheader("⚙️ 6 Formatting Options")
        
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
        st.subheader("🎛️ Darkness & Line Continuity Controller")
        st.write("Adjust this if lines appear too thick or if faint lines are missing.")
        darkness = st.slider("Sketch Darkness Threshold", min_value=50, max_value=230, value=150, step=10)
            
        st.markdown("---")
        
        if st.button("🚀 Generate Perfect BMP"):
            with st.spinner("Smoothing curves, connecting lines, and matching exact pixels..."):
                result = process_jacquard_perfect_curves(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(darkness)
                )
                
                if isinstance(result, str):
                    st.error("❌ An error occurred:")
                    st.code(result)
                else:
                    st.success("✅ BMP Generated Successfully! Lines are unbroken and perfectly curved.")
                    st.download_button(
                        label="📥 Download Smooth BMP",
                        data=result,
                        file_name="jacquard_perfect_design.bmp",
                        mime="image/bmp"
                    )
