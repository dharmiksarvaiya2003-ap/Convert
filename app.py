import streamlit as st
from PIL import Image
import numpy as np

def process_to_bmp(uploaded_file, width, height):
    img = Image.open(uploaded_file).convert("L")
    img = img.resize((width, height), Image.NEAREST)
    img_np = np.array(img)
    binary = np.where(img_np < 128, 0, 255).astype(np.uint8)
    
    # Blue Background (R:0, G:0, B:160)
    output = np.zeros((height, width, 3), dtype=np.uint8)
    output[:] = [0, 0, 160] 
    
    for y in range(height):
        for x in range(width):
            if binary[y, x] == 0: 
                output[y, x] = [255, 255, 0] # Yellow Figure
                # Red Outline Logic
                if x > 0 and binary[y, x-1] == 255:
                    output[y, x:x+2] = [255, 0, 0]
                if y > 0 and binary[y-1, x] == 255:
                    output[y, x] = [255, 0, 0]
    return Image.fromarray(output)

st.title("Jacquard BMP Converter")
uploaded_file = st.file_uploader("Upload JPG", type=['jpg', 'jpeg', 'png'])
w = st.number_input("Width", value=400)
h = st.number_input("Height", value=600)

if uploaded_file and st.button("Convert"):
    result = process_to_bmp(uploaded_file, w, h)
    result.save("design.bmp")
    with open("design.bmp", "rb") as f:
        st.download_button("Download BMP", f, "design.bmp", "image/bmp")
    st.image(result)

