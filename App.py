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
        
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if password == "DHARMIK@2025":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect Password.")
        return False
    return True

# --- 2. Advanced Image Processing Logic ---
def process_jacquard_exact_pixels(input_image, img_w, img_h, reed, pick, out_w, out_h, darkness_threshold, curve_smoothness):
    try:
        # Load and enhance contrast
        img = Image.open(input_image).convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.5)
        
        # Resize using high-quality Bilinear interpolation
        img_resized = img.resize((img_w, img_h), Image.Resampling.BILINEAR)
        data = np.array(img_resized)
        
        # Pre-blur to soften paper texture and rough pencil marks
        data = cv2.GaussianBlur(data, (3, 3), 0)
        
        # Threshold: Identify sketch lines
        _, bw_mask = cv2.threshold(data, darkness_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Close tiny gaps using a smooth elliptical kernel
        close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        bw_mask = cv2.morphologyEx(bw_mask, cv2.MORPH_CLOSE, close_kernel)
        
        # --- STEP 1: Raw Skeleton ---
        # Get the 1-pixel core line (this is usually jagged)
        raw_skeleton = cv2.ximgproc.thinning(bw_mask)
        
        # --- STEP 2: Geometric Curve Smoothing (The Fix) ---
        # mathematically removes zig-zags from the 1-pixel line
        if curve_smoothness > 0.0:
            contours, _ = cv2.findContours(raw_skeleton, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            smooth_skeleton = np.zeros_like(raw_skeleton)
            
            smooth_contours = []
            for cnt in contours:
                # Smooth out the jagged points
                approx = cv2.approxPolyDP(cnt, epsilon=curve_smoothness, closed=True)
                smooth_contours.append(approx)
                
            # Redraw as a mathematically perfect line (LINE_8)
            cv2.drawContours(smooth_skeleton, smooth_contours, -1, 255, 1, lineType=cv2.LINE_8)
            base_line = smooth_skeleton
        else:
            base_line = raw_skeleton
            
        # --- STEP 3: Exact Dilation with Elliptical Brush ---
        # Applies your exact out_w and out_h without making corners blocky
        out_w = max(1, int(out_w))
        out_h = max(1, int(out_h))
        thick_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (out_w, out_h))
        outline_mask = cv2.dilate(base_line, thick_kernel, iterations=1)
        
        # Create final image data array
        final_img_data = np.zeros((img_h, img_w), dtype=np.uint8)
        final_img_data[outline_mask > 0] = 1
        
        # Texcelle Palette: 0 = White, 1 = Red
        palette = [255, 255, 255, 255, 0, 0] + [255, 255, 255] * 254
        
        output_img = Image.fromarray(final_img_data, mode='P')
        output_img.putpalette(palette)
        
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
        st.title("🎨 Jacquard BMP Converter")
    with col_logout:
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Sketch (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.subheader("⚙️ Dimensions & Thickness")
        
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
        st.subheader("🎛️ Advanced Curve & Line Processing")
        
        darkness = st.slider("Darkness Threshold (Catches faint lines)", min_value=50, max_value=230, value=140, step=10)
        
        # NEW SLIDER FOR SMOOTHING
        smoothness = st.slider("Geometric Curve Smoothing (Removes zig-zags)", min_value=0.0, max_value=5.0, value=1.5, step=0.5)
            
        st.markdown("---")
        
        if st.button("🚀 Generate BMP"):
            with st.spinner("Processing smart curves..."):
                result = process_jacquard_exact_pixels(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(darkness), float(smoothness)
                )
                
                if isinstance(result, str):
                    st.error("❌ Error")
                    st.code(result)
                else:
                    st.success("✅ Success! Smooth curves applied.")
                    st.download_button(
                        label="📥 Download BMP",
                        data=result,
                        file_name="design.bmp",
                        mime="image/bmp"
                    )
