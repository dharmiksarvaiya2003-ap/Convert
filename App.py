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

# --- 2. THE PERFECT MATH LOGIC (માત્ર Right Side પિક્સેલ એડ કરવા માટે) ---
def add_pixels_exactly(image_1px, out_w, out_h):
    """
    આ ફંક્શન 1-પિક્સેલ ઈમેજ લેશે અને 
    તમે કહેશો એટલા જ પિક્સેલ જમણી બાજુ (out_w) અને નીચે (out_h) મુકશે.
    કોઈ વધારાના પિક્સેલ નહીં, કોઈ ખરાબ કર્વ નહીં.
    """
    h, w = image_1px.shape
    result = np.zeros((h, w), dtype=np.uint8)
    
    # 1-પિક્સેલ લાઈન ક્યાં ક્યાં છે તે શોધો
    y_coords, x_coords = np.where(image_1px > 0)
    
    # દરેક પિક્સેલને પકડીને કોપી કરો
    for dy in range(out_h):
        for dx in range(out_w):
            new_y = y_coords + dy
            new_x = x_coords + dx
            
            # ઈમેજની બહાર પિક્સેલ ન જાય તેની સાવચેતી
            valid = (new_x >= 0) & (new_x < w) & (new_y >= 0) & (new_y < h)
            
            # નવી જગ્યાએ પિક્સેલ મૂકો
            result[new_y[valid], new_x[valid]] = 255
            
    return result

# --- 3. MAIN PROCESSING LOGIC ---
def process_ultimate_bmp(input_image, img_w, img_h, reed, pick, out_w, out_h, threshold_val, mode):
    try:
        # 1. Image Load & Resize (સ્મૂધ કર્વ માટે)
        img_pil = Image.open(input_image).convert('RGB')
        img_cv = np.array(img_pil)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        
        # INTER_LANCZOS4 કર્વને ફાટવા નથી દેતું
        resized_gray = cv2.resize(gray, (img_w, img_h), interpolation=cv2.INTER_LANCZOS4)
        
        # 2. Thresholding
        _, binary = cv2.threshold(resized_gray, threshold_val, 255, cv2.THRESH_BINARY_INV)
        
        base_1px = np.zeros_like(binary)
        
        # 3. 1-Pixel પર્ફેક્ટ લાઈન બનાવવી
        if mode == "Solid Shape Outline":
            # સોલિડ માટે: એકદમ સળંગ અને 1-પિક્સેલ પાતળી બોર્ડર કાઢશે
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(base_1px, contours, -1, 255, 1) # '1' એટલે પર્ફેક્ટ 1 પિક્સેલ
        else:
            # સ્કેચ માટે
            kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
            closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close)
            base_1px = cv2.ximgproc.thinning(closed, thinningType=cv2.ximgproc.THINNING_GUOHALL)
            
        # 4. તમારું ફાઇનલ લોજીક: Width 2 એટલે માત્ર Right સાઈડ 1 પિક્સેલ એડ થશે
        final_mask = add_pixels_exactly(base_1px, out_w, out_h)
        
        # 5. Jacquard Color Palette (0=White, 1=Red)
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
    
    st.title("🎨 Exact Pixel Shift BMP Generator")
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
            with st.spinner("Processing Exact Pixels..."):
                result = process_ultimate_bmp(
                    uploaded_file, int(w), int(h), int(r), int(p), int(out_w), int(out_h), int(threshold_val), img_mode
                )
                
                if isinstance(result, str) and result.startswith("Error"):
                    st.error(f"❌ {result}")
                else:
                    st.success("✅ Success! પિક્સેલ એક્ઝેટ સેટ થઈ ગયા છે.")
                    st.download_button(
                        label="📥 Download BMP",
                        data=result,
                        file_name="final_exact_jacquard.bmp",
                        mime="image/bmp"
                    )
