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

# --- 2. Advanced Image Processing Logic for Smooth Curves ---
def process_jacquard_smooth_curves(input_image, img_w, img_h, reed, pick, out_w, out_h, darkness_threshold):
    try:
        # 1. Read Image directly into OpenCV
        file_bytes = np.asarray(bytearray(input_image.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
        
        # 2. High-Quality Resize (INTER_LANCZOS4 preserves curves much better than Bilinear)
        img_resized = cv2.resize(img, (img_w, img_h), interpolation=cv2.INTER_LANCZOS4)
        
        # 3. Pre-Smoothing (The Magic Step for Zig-Zag removal)
        # Blurs the pencil marks slightly so the edges become uniform before thresholding
        blurred = cv2.GaussianBlur(img_resized, (3, 3), 0)
        
        # 4. Threshold: Identify black sketch lines
        _, bw_mask = cv2.threshold(blurred, darkness_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # 5. Morphological Smoothing (Heal breaks & Smooth boundaries)
        # We use an Ellipse (circular) kernel instead of square for smoother ends
        morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        # Close: Fills micro-gaps so lines don't break
        bw_mask = cv2.morphologyEx(bw_mask, cv2.MORPH_CLOSE, morph_kernel)
        
        # Open: Removes tiny jagged spikes on the outside of the lines
        bw_mask = cv2.morphologyEx(bw_mask, cv2.MORPH_OPEN, morph_kernel)
        
        # 6. Advanced Thinning (Guo-Hall algorithm)
        # Guo-Hall is mathematically proven to maintain diagonal and curved lines 
        # much smoother than standard Zhang-Suen thinning.
        skeleton = cv2.ximgproc.thinning(bw_mask, thinningType=cv2.ximgproc.THINNING_GUOHALL)
        
        # 7. Apply Exact Custom Thickness using Elliptical Brush
        out_w = max(1, int(out_w))
        out_h = max(1, int(out_h))
        
        # Using MORPH_ELLIPSE prevents blocky, square 90-degree corners on curves
        thick_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (out_w, out_h))
        
        # If the size is 2x2 or less, fallback to RECT as ellipse math needs >2 to form a circle
        if out_w <= 2 and out_h <= 2:
             thick_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (out_w, out_h))
             
        outline_mask = cv2.dilate(skeleton, thick_kernel, iterations=1)
        
        # 8. Create final image data array (Background = 0)
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
        
        # Save to buffer with exact DPI matching Reed and Pick
        buf = io.BytesIO()
        output_img.save(buf, format="BMP", dpi=(reed, pick))
        return buf.getvalue()
        
    except Exception as e:
        return str(e)

# --- 3. Main Application UI ---
if check_password():
    st.set_page_config(page_title="Jacquard BMP Pro - Smooth Curves", layout="wide")
    
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("🎨 Jacquard BMP Converter (Pro)")
        st.write("Perfect Smooth Curves & Exact Thickness Generator for Texcelle")
    with col_logout:
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload your Sketch (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.subheader("⚙️ 6 Options: Texcelle Settings")
        
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
        st.subheader("🎛️ Darkness Controller")
        st.write("Adjust this slider if your pencil sketch is too light or has unwanted background noise.")
        darkness = st.slider("Sketch Darkness Threshold", min_value=50, max_value=230, value=150, step=10)
            
        st.markdown("---")
        
        if st.button("🚀 Generate Perfect BMP"):
            with st.spinner("Applying Anti-Zig-Zag Magic, Smoothing Curves & Formatting..."):
                result = process_jacquard_smooth_curves(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(darkness)
                )
                
                if isinstance(result, str):
                    st.error("❌ An error occurred:")
                    st.code(result)
                else:
                    st.success("✅ BMP Generated Successfully! Curves are Smooth, Lines are Continuous.")
                    st.download_button(
                        label="📥 Download Smooth BMP",
                        data=result,
                        file_name="jacquard_smooth_curves.bmp",
                        mime="image/bmp"
                    )
