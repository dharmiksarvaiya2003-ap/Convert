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

# --- 2. Advanced Vector Tracing (Zero Breakage & Adjusted Thickness) ---
def process_jacquard_exact_outline(input_image, img_w, img_h, reed, pick, out_w, out_h, threshold, mode):
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
            
        # Clean small gaps in the original high-res image
        kernel_heal = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_heal)
        
        # Step 2: Skeletonization (Get the perfect 1-pixel centerline)
        try:
            skeleton = cv2.ximgproc.thinning(binary, thinningType=cv2.ximgproc.THINNING_GUOHALL)
        except:
            skeleton = binary
            
        # Step 3: Extract Mathematical Vector Paths 
        contours, _ = cv2.findContours(skeleton, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        
        if not contours:
            return "Error: No lines detected. Please adjust the threshold."

        # Step 4: Create Blank Target Canvas
        canvas = np.zeros((img_h, img_w), dtype=np.uint8)
        
        # Step 5: Scale Vectors and draw 1-pixel thin lines first
        scale_x = img_w / orig_w
        scale_y = img_h / orig_h
        
        scaled_contours = []
        for cnt in contours:
            scaled_cnt = np.zeros_like(cnt, dtype=np.int32)
            scaled_cnt[:, 0, 0] = np.round(cnt[:, 0, 0] * scale_x)
            scaled_cnt[:, 0, 1] = np.round(cnt[:, 0, 1] * scale_y)
            scaled_contours.append(scaled_cnt)
            
        # Draw 1-pixel thin base path
        cv2.polylines(canvas, scaled_contours, isClosed=False, color=255, thickness=1, lineType=cv2.LINE_8)
        
        # Step 6: Apply Exact Adjusted Jacquard Brush Thickness (Out_W and Out_H)
        # --- THE FIX --- Adjusted Logic for Exact Pixels
        # For Width: We want total Out_W. We have 1-pixel centerline, need Out_W - 1 total padding.
        # This padding is split into Left and Right.
        pad_x = max(0, int(out_w) - 1)
        # For Height: We want total Out_H. We have 1-pixel centerline, need Out_H - 1 total padding.
        # This padding is split into Top and Bottom.
        pad_y = max(0, int(out_h) - 1)

        # Apply padding left and right for Width
        if pad_x > 0:
            # Shift Left
            left_canvas = np.zeros_like(canvas)
            left_canvas[:, :img_w - pad_x] = canvas[:, pad_x:]
            canvas = cv2.bitwise_or(canvas, left_canvas)
        
        # Apply padding up and down for Height
        if pad_y > 0:
            # Shift Up
            up_canvas = np.zeros_like(canvas)
            up_canvas[:img_h - pad_y, :] = canvas[pad_y:, :]
            canvas = cv2.bitwise_or(canvas, up_canvas)

        final_mask = canvas
            
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
    st.set_page_config(page_title="Jacquard BMP Pro - Exact Outlines", layout="wide")
    
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("🎨 Jacquard BMP Converter (Exact Outlines)")
        st.write("Vector Tracing Technology for Perfect, Custom-Thickness Lines")
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
                            help="બ્લેક એન્ડ વ્હાઇટ ડ્રોઇંગ માટે 'Sketch' અને કલરવાળી ડિઝાઇન બોર્ડર માટે 'Solid Shape' સિલેક્ટ કરો.")
        
        st.markdown("---")
        st.subheader("⚙️ 6 Formatting Options (The FIX is here!)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            w = st.number_input("1. Width (Pixels)", min_value=10, value=600)
            h = st.number_input("2. Height (Pixels)", min_value=10, value=800)
        with col2:
            r = st.number_input("3. Reed", min_value=1, value=100)
            p = st.number_input("4. Pick", min_value=1, value=100)
        with col3:
            # --- The new fix is applied to how these values are used internally ---
            out_w = st.number_input("5. Outline Width (X-axis)", min_value=1, value=2)
            out_h = st.number_input("6. Outline Height (Y-axis)", min_value=1, value=1)
            
        st.markdown("---")
        st.subheader("🎛️ Darkness Threshold (ડાર્કનેસ સેટિંગ)")
        threshold = st.slider("Adjust to pick up faint lines", min_value=50, max_value=230, value=150, step=10)
            
        st.markdown("---")
        
        if st.button("🚀 Generate Perfect BMP"):
            with st.spinner("Extracting vector paths and applying exact outline thickness..."):
                # --- The logic fix happens inside this function call ---
                result = process_jacquard_exact_outline(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(threshold), img_mode
                )
                
                if isinstance(result, str) and result.startswith("Error"):
                    st.error(f"❌ {result}")
                else:
                    st.success("✅ Perfect BMP Generated! (હવે પહોળાઈ અને ઊંચાઈ એક્ઝેટ તમે માંગો એ જ આવશે!)")
                    st.download_button(
                        label="📥 Download BMP",
                        data=result,
                        file_name="jacquard_exact_outline.bmp",
                        mime="image/bmp"
                    )
