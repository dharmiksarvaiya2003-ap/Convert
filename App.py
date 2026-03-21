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

# --- 2. Guarantee 1-Pixel Base ---
def get_1px_skeleton(img):
    try:
        # Use Zhang-Suen for perfect 1-pixel skeleton
        return cv2.ximgproc.thinning(img, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
    except:
        # Mathematical fallback
        size = np.size(img)
        skel = np.zeros(img.shape, np.uint8)
        ret, img_bin = cv2.threshold(img, 127, 255, 0)
        element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
        done = False
        while(not done):
            eroded = cv2.erode(img_bin, element)
            temp = cv2.dilate(eroded, element)
            temp = cv2.subtract(img_bin, temp)
            skel = cv2.bitwise_or(skel, temp)
            img_bin = eroded.copy()
            zeros = size - cv2.countNonZero(img_bin)
            if zeros == size:
                done = True
        return skel

# --- 3. THE FIX: Exact Pixel Expansion (Shift & Merge) ---
def exact_pixel_expansion(binary_img, target_w, target_h):
    """
    This completely fixes the +1 pixel error.
    It takes the 1-px base line and copies it exactly (target_w - 1) times 
    to the right, and (target_h - 1) times down.
    """
    h, w = binary_img.shape
    result = np.zeros((h, w), dtype=np.uint8)
    
    # Loop exactly target_w and target_h times
    for dy in range(target_h):
        for dx in range(target_w):
            # Transformation matrix to shift pixels
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            shifted = cv2.warpAffine(binary_img, M, (w, h), flags=cv2.INTER_NEAREST)
            # Combine the shifted pixels
            result = cv2.bitwise_or(result, shifted)
            
    return result

# --- 4. Main Processing Logic ---
def process_jacquard_perfect(input_image, img_w, img_h, reed, pick, out_w, out_h, threshold_val, mode):
    try:
        img_pil = Image.open(input_image).convert('RGB')
        img_cv = np.array(img_pil)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        
        # Resize first
        gray_resized = cv2.resize(gray, (img_w, img_h), interpolation=cv2.INTER_LANCZOS4)
        
        # Get STRICTLY 1-pixel thick lines
        if mode == "Sketch Lines (સ્કેચ માટે)":
            _, binary = cv2.threshold(gray_resized, threshold_val, 255, cv2.THRESH_BINARY_INV)
            base_1px = get_1px_skeleton(binary)
        else:
            edges = cv2.Canny(gray_resized, threshold_val, int(threshold_val * 1.5))
            # Close small gaps before extracting skeleton
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (2, 2))
            closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            base_1px = get_1px_skeleton(closed_edges)
            
        # Apply the exact mathematical expansion (W x H)
        final_mask = exact_pixel_expansion(base_1px, int(out_w), int(out_h))
        
        # Color Mapping
        final_img_data = np.zeros((img_h, img_w), dtype=np.uint8)
        final_img_data[final_mask > 0] = 1 
        
        # Jacquard Palette (0=White background, 1=Red design)
        palette = [
            255, 255, 255,  
            255, 0, 0,      
        ]
        palette += [255, 255, 255] * 254
        
        output_img = Image.fromarray(final_img_data, mode='P')
        output_img.putpalette(palette)
        
        buf = io.BytesIO()
        output_img.save(buf, format="BMP", dpi=(reed, pick))
        return buf.getvalue()
        
    except Exception as e:
        return f"Error: {str(e)}"

# --- 5. User Interface ---
if check_password():
    st.set_page_config(page_title="Jacquard BMP Pro", layout="wide")
    
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("🎨 Jacquard BMP Converter (Flawless Dimensions)")
    with col_logout:
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Image (JPG/PNG/BMP)", type=["jpg", "jpeg", "png", "bmp"])
    
    if uploaded_file is not None:
        
        img_mode = st.radio("Image Type (ઇમેજનો પ્રકાર)", 
                            ["Sketch Lines (સ્કેચ માટે)", "Solid Shape Outline (સોલિડ ડિઝાઇન માટે)"])
        
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
        threshold_val = st.slider("Darkness Threshold", min_value=50, max_value=230, value=150, step=10)
            
        st.markdown("---")
        
        if st.button("🚀 Generate Perfect BMP"):
            with st.spinner("Processing Exact Dimensions..."):
                result = process_jacquard_perfect(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(threshold_val), img_mode
                )
                
                if isinstance(result, str) and result.startswith("Error"):
                    st.error(f"❌ {result}")
                else:
                    st.success(f"✅ Success! (Outline Exactly {out_w}x{out_h})")
                    st.download_button(
                        label="📥 Download BMP",
                        data=result,
                        file_name="perfect_jacquard_design.bmp",
                        mime="image/bmp"
                    )
