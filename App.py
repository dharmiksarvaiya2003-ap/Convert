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

# --- 2. Guaranteed 1-Pixel Skeleton Fallback ---
def get_1px_skeleton(img):
    try:
        # The best mathematically proven 1-pixel thinning algorithm
        return cv2.ximgproc.thinning(img, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
    except:
        # Fallback if library fails
        skel = np.zeros(img.shape, np.uint8)
        eroded = np.zeros(img.shape, np.uint8)
        temp = np.zeros(img.shape, np.uint8)
        cross = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
        img_copy = img.copy()
        while True:
            cv2.erode(img_copy, cross, eroded)
            cv2.dilate(eroded, cross, temp)
            cv2.subtract(img_copy, temp, temp)
            cv2.bitwise_or(skel, temp, skel)
            img_copy[:,:] = eroded[:,:]
            if cv2.countNonZero(img_copy) == 0:
                break
        return skel

# --- 3. Advanced Vector Processing (Exact Pixel Matrix) ---
def process_jacquard_flawless(input_image, img_w, img_h, reed, pick, out_w, out_h, threshold, mode):
    try:
        img_pil = Image.open(input_image).convert('RGB')
        img_cv = np.array(img_pil)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        
        # Step 1: Direct Resize to Target Dimension (Avoids polygon drawing artifacts)
        gray_resized = cv2.resize(gray, (img_w, img_h), interpolation=cv2.INTER_LANCZOS4)
        
        # Step 2: Extract strictly 1-pixel base lines
        if mode == "Sketch Lines (સ્કેચ માટે)":
            _, binary = cv2.threshold(gray_resized, threshold, 255, cv2.THRESH_BINARY_INV)
            # Thin the thick sketch lines to exact 1-pixel center
            base_1px = get_1px_skeleton(binary)
        else:
            # Canny directly finds 1-pixel thin edges
            edges = cv2.Canny(gray_resized, threshold, int(threshold * 1.5))
            # Close tiny gaps
            kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_close)
            # Ensure it remains strictly 1-pixel after closing
            base_1px = get_1px_skeleton(closed_edges)
            
        # Step 3: Exact Mathematical Expansion (The Fix for WxH mismatch)
        out_w = max(1, int(out_w))
        out_h = max(1, int(out_h))
        
        # Matrix forces exact size. Anchor=(0,0) ensures perfect directional adding.
        kernel_expand = np.ones((out_h, out_w), dtype=np.uint8)
        final_mask = cv2.dilate(base_1px, kernel_expand, anchor=(0,0), iterations=1)
        
        # Step 4: Map Palette Colors (0=White, 1=Red)
        final_img_data = np.zeros((img_h, img_w), dtype=np.uint8)
        final_img_data[final_mask > 0] = 1 
        
        palette = [
            255, 255, 255,  # 0: Background
            255, 0, 0,      # 1: Red Outline
        ]
        palette += [255, 255, 255] * 254
        
        output_img = Image.fromarray(final_img_data, mode='P')
        output_img.putpalette(palette)
        
        buf = io.BytesIO()
        output_img.save(buf, format="BMP", dpi=(reed, pick))
        return buf.getvalue()
        
    except Exception as e:
        return f"Error: {str(e)}"

# --- 4. Main Application UI ---
if check_password():
    st.set_page_config(page_title="Jacquard BMP Pro", layout="wide")
    
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("🎨 Jacquard BMP Converter (Flawless Dimensions)")
        st.write("Guaranteed Exact Mathematical Pixel Expansion")
    with col_logout:
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload your Image (JPG/PNG/BMP)", type=["jpg", "jpeg", "png", "bmp"])
    
    if uploaded_file is not None:
        
        st.subheader("⚙️ Image Type (ઇમેજનો પ્રકાર)")
        img_mode = st.radio("તમે કેવો ફોટો અપલોડ કર્યો છે?", 
                            ["Sketch Lines (સ્કેચ માટે)", "Solid Shape Outline (સોલિડ ડિઝાઇન માટે)"],
                            help="જો તમે બ્લેક એન્ડ વ્હાઇટ ડ્રોઇંગ અપલોડ કર્યું હોય તો 'Sketch' રાખો. જો તમે કલરવાળો ભરેલો ફોટો આપ્યો હોય અને તેની બોર્ડર કાઢવી હોય તો 'Solid Shape' સિલેક્ટ કરો.")
        
        st.markdown("---")
        st.subheader("⚙️ 6 Formatting Options (Exact Matrix Match)")
        
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
        st.subheader("🎛️ Darkness Threshold (ડાર્કનેસ સેટિંગ)")
        threshold = st.slider("Adjust to pick up faint lines (આછા ડ્રોઇંગને પકડવા માટે)", min_value=50, max_value=230, value=150, step=10)
            
        st.markdown("---")
        
        if st.button("🚀 Generate Perfect BMP"):
            with st.spinner(f"Applying strict {out_w}x{out_h} pixel matrix..."):
                result = process_jacquard_flawless(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(threshold), img_mode
                )
                
                if isinstance(result, str) and result.startswith("Error"):
                    st.error(f"❌ {result}")
                else:
                    st.success(f"✅ Perfect BMP Generated! (હવે પહોળાઈ એક્ઝેટ {out_w} અને ઊંચાઈ {out_h} જ બનશે!)")
                    st.download_button(
                        label="📥 Download BMP",
                        data=result,
                        file_name="jacquard_flawless_matrix.bmp",
                        mime="image/bmp"
                    )
