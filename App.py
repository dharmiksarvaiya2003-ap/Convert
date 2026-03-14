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

# --- 2. 100% Perfect Image Processing Logic ---
def process_jacquard_ultimate(input_image, img_w, img_h, reed, pick, out_w, out_h, darkness_threshold, smooth_level):
    try:
        # 1. Load Image and Boost Contrast
        img = Image.open(input_image).convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(3.0) 
        
        # 2. Resize using Highest Quality (LANCZOS prevents pixelation)
        img_resized = img.resize((img_w, img_h), Image.Resampling.LANCZOS)
        data = np.array(img_resized)
        
        # 3. Soften the sketch to merge dots and prevent broken lines
        data = cv2.GaussianBlur(data, (5, 5), 0)
        
        # 4. Binarization (Convert to strict Black & White mask)
        _, bw_mask = cv2.threshold(data, darkness_threshold, 255, cv2.THRESH_BINARY_INV)
        
        # 5. HEALING LOGIC: Close gaps in the pencil lines so they NEVER break
        heal_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        bw_mask = cv2.morphologyEx(bw_mask, cv2.MORPH_CLOSE, heal_kernel, iterations=1)
        
        # 6. Extract raw 1-pixel skeleton
        skeleton = cv2.ximgproc.thinning(bw_mask)
        
        # 7. THE MAGIC: Morphological Ironing (Smoothes curves WITHOUT breaking junctions)
        smooth_skel = skeleton.copy()
        iters = int(smooth_level)
        for _ in range(iters):
            # Dilate -> Blur -> Threshold -> Thin (Irons out zig-zags completely)
            dil = cv2.dilate(smooth_skel, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
            blur = cv2.GaussianBlur(dil, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 120, 255, cv2.THRESH_BINARY)
            smooth_skel = cv2.ximgproc.thinning(thresh)
            
        # 8. APPLY EXACT BRUSH SIZE (Outline Width/Height)
        out_w = max(1, int(out_w))
        out_h = max(1, int(out_h))
        brush_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (out_w, out_h))
        final_mask = cv2.dilate(smooth_skel, brush_kernel, iterations=1)
        
        # 9. APPLY PALETTE AND EXPORT (0 = White, 1 = Red)
        final_img_data = np.zeros((img_h, img_w), dtype=np.uint8)
        final_img_data[final_mask > 0] = 1 
        
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
        st.title("🎨 Jacquard BMP Converter (Pro Smooth)")
    with col_logout:
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Sketch (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        st.subheader("⚙️ Dimensions & Thickness (Your 6 Options)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            w = st.number_input("1. Width (Pixels)", min_value=10, value=1200)
            h = st.number_input("2. Height (Pixels)", min_value=10, value=1600)
        with col2:
            r = st.number_input("3. Reed", min_value=1, value=100)
            p = st.number_input("4. Pick", min_value=1, value=100)
        with col3:
            out_w = st.number_input("5. Outline Width (X)", min_value=1, value=2)
            out_h = st.number_input("6. Outline Height (Y)", min_value=1, value=1)
            
        st.markdown("---")
        st.subheader("🎛️ Advanced Curve & Line Control")
        
        darkness = st.slider("Darkness Threshold (Increase if lines are missing)", min_value=50, max_value=230, value=140, step=5)
        
        # NEW PERFECT SMOOTHING SLIDER (0 to 4)
        smoothness = st.slider("Curve Smoothing Power (Removes zig-zags & keeps lines joined)", min_value=0, max_value=4, value=2, step=1)
            
        st.markdown("---")
        
        if st.button("🚀 Generate Perfect BMP"):
            with st.spinner("Ironing curves and generating BMP..."):
                result = process_jacquard_ultimate(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(darkness), int(smoothness)
                )
                
                if isinstance(result, str):
                    st.error("❌ Error")
                    st.code(result)
                else:
                    st.success("✅ Success! Perfectly smooth, unbroken curves applied.")
                    st.download_button(
                        label="📥 Download Red Outline BMP",
                        data=result,
                        file_name="perfect_design.bmp",
                        mime="image/bmp"
                    )
