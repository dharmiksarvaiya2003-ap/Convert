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

# --- 2. STRICT 1-PIXEL GENERATOR (Removes all overlapping joints) ---
def get_strict_8connected_skeleton(binary_img):
    # Ensure binary image
    _, bin_img = cv2.threshold(binary_img, 127, 255, cv2.THRESH_BINARY)
    
    # 1. Apply Zhang-Suen thinning (Best for 1-pixel skeleton)
    skeleton = cv2.ximgproc.thinning(bin_img, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
    
    # 2. Paranoid Cleanup: Break any 2x2 blocks or 'L' joints left over
    # This prevents the +1 pixel expansion error at corners!
    h, w = skeleton.shape
    for y in range(h - 1):
        for x in range(w - 1):
            if skeleton[y, x] and skeleton[y+1, x] and skeleton[y, x+1] and skeleton[y+1, x+1]:
                skeleton[y+1, x+1] = 0 # Break the block
    return skeleton

# --- 3. MAIN PROCESSING LOGIC ---
def process_jacquard_ultimate_fixed(input_image, img_w, img_h, reed, pick, out_w, out_h, threshold_val, mode):
    try:
        img_pil = Image.open(input_image).convert('RGB')
        img_cv = np.array(img_pil)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        
        # Resize first
        gray_resized = cv2.resize(gray, (img_w, img_h), interpolation=cv2.INTER_LANCZOS4)
        
        # Binarize
        _, binary = cv2.threshold(gray_resized, threshold_val, 255, cv2.THRESH_BINARY_INV)
        
        if mode == "Solid Shape Outline (સોલિડ ડિઝાઇન માટે)":
            # Get purely the outer boundary
            kernel_3 = np.ones((3,3), np.uint8)
            dilated_shape = cv2.dilate(binary, kernel_3, iterations=1)
            boundary = cv2.subtract(dilated_shape, binary)
            # Thin boundary to strictly 1 pixel
            base_1px = get_strict_8connected_skeleton(boundary)
        else:
            # Sketch lines: thin directly
            base_1px = get_strict_8connected_skeleton(binary)
        
        # --- THE 100% FIX FOR EXACT WIDTH & HEIGHT ---
        # Create a kernel of EXACTLY the user's requested dimensions
        expand_kernel = np.ones((out_h, out_w), dtype=np.uint8)
        
        # Dilate using anchor=(0,0) (Top-Left corner)
        # This mathematically forces a 1-pixel dot to become EXACTLY out_w x out_h.
        # It will NEVER exceed the specified numbers.
        final_mask = cv2.dilate(base_1px, expand_kernel, anchor=(0,0), iterations=1)
        
        # Color Mapping for Jacquard
        final_img_data = np.zeros((img_h, img_w), dtype=np.uint8)
        final_img_data[final_mask > 0] = 1 
        
        # Palette: 0=White, 1=Red
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

# --- 4. USER INTERFACE ---
if check_password():
    st.set_page_config(page_title="Jacquard BMP Pro", layout="wide")
    
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("🎨 Jacquard BMP Converter (100% Guaranteed Dimensions)")
    with col_logout:
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Image (JPG/PNG/BMP)", type=["jpg", "jpeg", "png", "bmp"])
    
    if uploaded_file is not None:
        
        img_mode = st.radio("Image Type (તમે કેવો ફોટો અપલોડ કર્યો છે?)", 
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
            with st.spinner("Calculating Exact Pixels..."):
                result = process_jacquard_ultimate_fixed(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(threshold_val), img_mode
                )
                
                if isinstance(result, str) and result.startswith("Error"):
                    st.error(f"❌ {result}")
                else:
                    st.success(f"✅ Success! (Outline is mathematically FIXED to exactly {out_w}x{out_h})")
                    st.download_button(
                        label="📥 Download BMP",
                        data=result,
                        file_name="perfect_jacquard_design.bmp",
                        mime="image/bmp"
                    )
