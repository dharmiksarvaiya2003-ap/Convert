import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io

# --- 1. Password System ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.set_page_config(page_title="Jacquard Pro - Login", layout="centered")
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

# --- 2. EXACT PIXEL SHIFT LOGIC (100% Right-Side Strict Addition) ---
def add_pixels_exactly(image_1px, out_w, out_h):
    h, w = image_1px.shape
    result = np.zeros((h, w), dtype=np.uint8)
    
    y_coords, x_coords = np.where(image_1px > 0)
    
    for dy in range(out_h):
        for dx in range(out_w):
            new_y = y_coords + dy
            new_x = x_coords + dx
            
            valid = (new_x >= 0) & (new_x < w) & (new_y >= 0) & (new_y < h)
            result[new_y[valid], new_x[valid]] = 255
            
    return result

# --- 3. MAIN PROCESSING LOGIC (CANNY EDGE FOR PERFECT CURVES) ---
def process_ultimate_bmp(input_image, img_w, img_h, reed, pick, out_w, out_h, threshold_val, mode):
    try:
        img_pil = Image.open(input_image).convert('RGB')
        img_cv = np.array(img_pil)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        
        # INTER_CUBIC is best for maintaining smooth, continuous curves during resize
        resized_gray = cv2.resize(gray, (img_w, img_h), interpolation=cv2.INTER_CUBIC)
        
        base_1px = np.zeros((img_h, img_w), dtype=np.uint8)
        
        if mode == "Solid Shape Outline":
            # Canny Edge: Guarantees STRICTLY 1-pixel thin, sharp, and connected curves.
            # No clumping of pixels allowed.
            blurred = cv2.GaussianBlur(resized_gray, (3, 3), 0)
            base_1px = cv2.Canny(blurred, threshold_val, threshold_val + 50)
        else:
            # For Sketch lines: strict Zhang-Suen thinning
            _, binary = cv2.threshold(resized_gray, threshold_val, 255, cv2.THRESH_BINARY_INV)
            base_1px = cv2.ximgproc.thinning(binary, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
            
        # Add width/height EXACTLY as requested (e.g. w=2, h=1 means +1 pixel to the right only)
        final_mask = add_pixels_exactly(base_1px, out_w, out_h)
        
        # Jacquard Color Palette (0=White background, 1=Red design)
        final_img_data = np.zeros((img_h, img_w), dtype=np.uint8)
        final_img_data[final_mask > 0] = 1 
        
        palette = [255, 255, 255, 255, 0, 0] + [255, 255, 255] * 254
        
        output_img = Image.fromarray(final_img_data, mode='P')
        output_img.putpalette(palette)
        
        buf = io.BytesIO()
        output_img.save(buf, format="BMP", dpi=(reed, pick))
        return buf.getvalue()
        
    except Exception as e:
        return f"Error: {str(e)}"

# --- 4. USER INTERFACE ---
if check_password():
    st.set_page_config(page_title="Jacquard Master", layout="wide")
    
    st.title("🎨 Perfect Curve BMP Generator")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "bmp"])
    
    if uploaded_file is not None:
        
        img_mode = st.radio("Image Type:", ["Solid Shape Outline", "Sketch Lines"])
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            w = st.number_input("Width (Pixels)", min_value=10, value=600)
            h = st.number_input("Height (Pixels)", min_value=10, value=800)
        with col2:
            r = st.number_input("Reed", min_value=1, value=100)
            p = st.number_input("Pick", min_value=1, value=100)
        with col3:
            out_w = st.number_input("Outline Width (X-axis)", min_value=1, value=2)
            out_h = st.number_input("Outline Height (Y-axis)", min_value=1, value=1)
            
        st.markdown("---")
        threshold_val = st.slider("Darkness Threshold", 50, 230, 150)
            
        if st.button("🚀 Generate Perfect BMP"):
            with st.spinner("Processing Strict 1-Pixel Edges..."):
                result = process_ultimate_bmp(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(threshold_val), img_mode
                )
                
                if isinstance(result, str) and result.startswith("Error"):
                    st.error(f"❌ {result}")
                else:
                    st.success("✅ Success! પિક્સેલ વધ્યા વગર, એક્ઝેટ શાર્પ કર્વ સેટ થઈ ગયા છે.")
                    st.download_button(
                        label="📥 Download BMP",
                        data=result,
                        file_name="ultimate_sharp_jacquard.bmp",
                        mime="image/bmp"
                    )
