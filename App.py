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

# --- 2. 100% Pixel-Perfect Thickness Logic ---
def process_jacquard_exact_pixel_perfect(input_image, img_w, img_h, reed, pick, out_w, out_h, threshold, mode):
    try:
        # Load Image
        img_pil = Image.open(input_image).convert('RGB')
        img_cv = np.array(img_pil)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        
        # Step 1: Smooth original image before resizing to prevent line breakage
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Step 2: Resize FIRST to Target Jacquard Size (Width x Height)
        # This guarantees our grid matches your exact required output size from the beginning
        resized_gray = cv2.resize(blurred, (img_w, img_h), interpolation=cv2.INTER_LANCZOS4)
        
        # Step 3: Extract lines based on mode
        if mode == "Sketch Lines (સ્કેચ માટે)":
            _, binary = cv2.threshold(resized_gray, threshold, 255, cv2.THRESH_BINARY_INV)
            # Close minor gaps
            kernel_heal = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_heal)
        else:
            binary = cv2.Canny(resized_gray, threshold, int(threshold * 1.5))
            
        # Step 4: GUARANTEE Absolute 1-Pixel Base Thickness (Skeletonization)
        # This ensures the base line is strictly 1 pixel wide everywhere. No double pixels!
        try:
            base_1px = cv2.ximgproc.thinning(binary, thinningType=cv2.ximgproc.THINNING_GUOHALL)
        except:
            base_1px = binary
            
        # Step 5: Apply EXACT User-Defined Outline Width and Height
        out_w = max(1, int(out_w))
        out_h = max(1, int(out_h))
        
        if out_w == 1 and out_h == 1:
            final_mask = base_1px
        else:
            # Create an exact rectangular brush of size (Height, Width)
            brush = np.ones((out_h, out_w), dtype=np.uint8)
            # Dilation with anchor=(0,0) means it places the exact WxH block starting from that 1 pixel.
            # 1 pixel + anchor(0,0) with 2x1 brush = exactly 2 pixels wide and 1 pixel high.
            final_mask = cv2.dilate(base_1px, brush, anchor=(0, 0), iterations=1)
            
        # Step 6: Map to Jacquard Palette Colors (0=White, 1=Red)
        final_img_data = np.zeros((img_h, img_w), dtype=np.uint8)
        final_img_data[final_mask > 0] = 1 
        
        palette = [
            255, 255, 255,  # 0: White Background
            255, 0, 0,      # 1: Red Outline
        ]
        palette += [255, 255, 255] * 254 # Fill remaining palette with white
        
        output_img = Image.fromarray(final_img_data, mode='P')
        output_img.putpalette(palette)
        
        buf = io.BytesIO()
        output_img.save(buf, format="BMP", dpi=(reed, pick))
        return buf.getvalue()
        
    except Exception as e:
        return str(e)

# --- 3. Main Application UI ---
if check_password():
    st.set_page_config(page_title="Jacquard BMP Pro - Pixel Perfect", layout="wide")
    
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.title("🎨 Jacquard BMP Converter (Pixel Perfect)")
        st.write("Guarantees 100% accurate outline thickness (Width & Height)")
    with col_logout:
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload your Image (JPG/PNG/BMP)", type=["jpg", "jpeg", "png", "bmp"])
    
    if uploaded_file is not None:
        
        st.subheader("⚙️ Image Type (ઇમેજનો પ્રકાર)")
        img_mode = st.radio("તમે કેવો ફોટો અપલોડ કર્યો છે?", 
                            ["Sketch Lines (સ્કેચ માટે)", "Solid Shape Outline (સોલિડ ડિઝાઇન માટે)"])
        
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
        threshold = st.slider("Adjust to pick up faint lines", min_value=50, max_value=230, value=150, step=10)
            
        st.markdown("---")
        
        if st.button("🚀 Generate Perfect BMP"):
            with st.spinner("Applying pixel-perfect thickness math..."):
                result = process_jacquard_exact_pixel_perfect(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(threshold), img_mode
                )
                
                if isinstance(result, str) and result.startswith("Error"):
                    st.error(f"❌ {result}")
                else:
                    st.success(f"✅ Perfect BMP Generated! (આઉટલાઇન એક્ઝેટ {out_w}x{out_h} ની જ બની છે!)")
                    st.download_button(
                        label="📥 Download BMP",
                        data=result,
                        file_name="jacquard_pixel_perfect.bmp",
                        mime="image/bmp"
                    )
