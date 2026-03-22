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

# --- 2. EXACT PIXEL SHIFT LOGIC (The Magic Fix) ---
def expand_line_precisely(base_img, target_w, target_h):
    """
    This function takes a 1-pixel thick line and strictly copies it 
    to the right (target_w) and bottom (target_h) without ANY diagonal 3x2 errors.
    If target_w=2 and target_h=1: It only adds 1 pixel to the right.
    """
    h, w = base_img.shape
    result = np.zeros_like(base_img)
    
    for dy in range(target_h):
        for dx in range(target_w):
            # Shift the image exactly by dx (right) and dy (down)
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            shifted = cv2.warpAffine(base_img, M, (w, h), flags=cv2.INTER_NEAREST)
            # Add the shifted pixels to the result
            result = cv2.bitwise_or(result, shifted)
            
    return result

# --- 3. MAIN PROCESSING LOGIC ---
def process_perfect_bmp(input_image, img_w, img_h, reed, pick, out_w, out_h, threshold_val, mode):
    try:
        # Load and resize smoothly to maintain curves
        img_pil = Image.open(input_image).convert('RGB')
        img_cv = np.array(img_pil)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        resized_gray = cv2.resize(gray, (img_w, img_h), interpolation=cv2.INTER_LANCZOS4)
        
        # Blur slightly to fix rough edges before processing
        blurred = cv2.GaussianBlur(resized_gray, (3, 3), 0)
        
        # Binarize
        _, binary = cv2.threshold(blurred, threshold_val, 255, cv2.THRESH_BINARY_INV)
        
        base_1px = np.zeros_like(binary)
        
        if mode == "Solid Shape Outline (સોલિડ ડિઝાઇન માટે)":
            # 1. Get exact continuous outer boundary (STRICTLY 1-pixel thick)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(base_1px, contours, -1, 255, 1) # 1 means 1-pixel thickness
        else:
            # 2. For sketches: Fill gaps first, then thin to 1 pixel (Guo-Hall is best for curves)
            kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
            closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close)
            base_1px = cv2.ximgproc.thinning(closed, thinningType=cv2.ximgproc.THINNING_GUOHALL)
            
        # --- APPLY EXACT WIDTH & HEIGHT ---
        final_mask = expand_line_precisely(base_1px, out_w, out_h)
        
        # Color Mapping: 0=White, 1=Red
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
    st.set_page_config(page_title="Jacquard BMP - Ultimate Fix", layout="wide")
    
    st.title("🎨 Perfect Jacquard BMP (Exact Pixel Control)")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "bmp"])
    
    if uploaded_file is not None:
        
        img_mode = st.radio("Select Image Type:", 
                            ["Solid Shape Outline (સોલિડ ડિઝાઇન માટે)", "Sketch Lines (સ્કેચ માટે)"])
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            w = st.number_input("1. Width (Pixels)", min_value=10, value=600)
            h = st.number_input("2. Height (Pixels)", min_value=10, value=800)
        with col2:
            r = st.number_input("3. Reed", min_value=1, value=100)
            p = st.number_input("4. Pick", min_value=1, value=100)
        with col3:
            out_w = st.number_input("5. Outline Width (X-axis)", min_value=1, value=2)
            out_h = st.number_input("6. Outline Height (Y-axis)", min_value=1, value=1)
            
        st.markdown("---")
        threshold_val = st.slider("Darkness Threshold (લાઈન પકડવા માટે)", 50, 230, 150)
            
        st.markdown("---")
        
        if st.button("🚀 Generate BMP"):
            with st.spinner("Processing Exact Pixels..."):
                result = process_perfect_bmp(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(threshold_val), img_mode
                )
                
                if isinstance(result, str) and result.startswith("Error"):
                    st.error(f"❌ {result}")
                else:
                    st.success("✅ Success! પિક્સેલ એક્ઝેટ સેટ થઈ ગયા છે.")
                    st.download_button(
                        label="📥 Download BMP",
                        data=result,
                        file_name="ultimate_perfect_jacquard.bmp",
                        mime="image/bmp"
                    )
