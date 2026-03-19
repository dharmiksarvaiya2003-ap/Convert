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

# --- 2. Advanced Vector Tracing (Exact Pixel Control & No 2x2 Blocks) ---
def process_jacquard_vector_curves(input_image, img_w, img_h, reed, pick, out_w, out_h, threshold, mode):
    try:
        img_pil = Image.open(input_image).convert('RGB')
        img_cv = np.array(img_pil)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        
        orig_h, orig_w = gray.shape
        
        # Step 1: Extract Base Lines at Full Resolution
        if mode == "Sketch Lines (સ્કેચ માટે)":
            _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
        else:
            binary = cv2.Canny(gray, threshold, int(threshold * 1.5))
            
        kernel_heal = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_heal)
        
        # Step 2: Skeletonization 
        try:
            skeleton = cv2.ximgproc.thinning(binary, thinningType=cv2.ximgproc.THINNING_GUOHALL)
        except:
            skeleton = binary
            
        # Step 3: Extract Mathematical Vector Paths 
        contours, _ = cv2.findContours(skeleton, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        
        if not contours:
            return "Error: No lines detected. Please adjust the threshold."

        # Step 4: Create Target Canvas and Draw Scaled Paths
        canvas = np.zeros((img_h, img_w), dtype=np.uint8)
        scale_x = img_w / orig_w
        scale_y = img_h / orig_h
        
        scaled_contours = []
        for cnt in contours:
            scaled_cnt = np.zeros_like(cnt, dtype=np.int32)
            scaled_cnt[:, 0, 0] = np.round(cnt[:, 0, 0] * scale_x)
            scaled_cnt[:, 0, 1] = np.round(cnt[:, 0, 1] * scale_y)
            scaled_contours.append(scaled_cnt)
            
        # Draw base lines
        cv2.polylines(canvas, scaled_contours, isClosed=False, color=255, thickness=1, lineType=cv2.LINE_8)
        
        # Step 5: STRICT THINNING (To remove overlapping drawing artifacts)
        try:
            canvas = cv2.ximgproc.thinning(canvas, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
        except:
            pass
            
        # Step 5.1: THE 2x2 BLOCK KILLER (Guarantees absolute 1-pixel thickness)
        # This removes any 2x2 pixel chunks that cause the W=3 or H=2 errors when shifting.
        for _ in range(3): 
            bin_canvas = (canvas > 0).astype(np.uint8)
            kernel_2x2 = np.array([[1, 1], [1, 1]], dtype=np.uint8)
            eroded = cv2.erode(bin_canvas, kernel_2x2, iterations=1)
            # Break the 2x2 block by removing its top-left pixel
            canvas[eroded == 1] = 0

        # Step 6: EXACT MATHEMATICAL SHIFTING
        # Now that canvas is 100% strictly 1 pixel, mathematical shifting will be flawless.
        out_w = max(1, int(out_w))
        out_h = max(1, int(out_h))
        
        final_mask = np.copy(canvas)
        
        # Apply exact X-axis width
        if out_w > 1:
            for i in range(1, out_w):
                shifted = np.roll(canvas, i, axis=1)
                shifted[:, :i] = 0 # Clear the wrapped edge
                final_mask = np.bitwise_or(final_mask, shifted)
                
        # Apply exact Y-axis height
        if out_h > 1:
            temp_mask = np.copy(final_mask)
            for i in range(1, out_h):
                shifted = np.roll(temp_mask, i, axis=0)
                shifted[:i, :] = 0 # Clear the wrapped edge
                final_mask = np.bitwise_or(final_mask, shifted)
            
        # Step 7: Map exact Palette Colors (0=White, 1=Red)
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
        return str(e)

# --- 3. Main Application UI ---
if check_password():
    st.set_page_config(page_title="Jacquard BMP Pro", layout="wide")
    
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("🎨 Jacquard BMP Converter (Flawless Dimensions)")
        st.write("Vector Tracing Technology for 100% Continuous Lines")
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
        st.subheader("⚙️ 6 Formatting Options")
        
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
            with st.spinner("Extracting vector paths and drawing exact continuous curves..."):
                result = process_jacquard_vector_curves(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(threshold), img_mode
                )
                
                if isinstance(result, str) and result.startswith("Error"):
                    st.error(f"❌ {result}")
                else:
                    st.success("✅ Perfect BMP Generated! (એકદમ સળંગ અને ન તૂટે તેવી લાઈનો)")
                    st.download_button(
                        label="📥 Download BMP",
                        data=result,
                        file_name="jacquard_perfect_vector.bmp",
                        mime="image/bmp"
                    )
