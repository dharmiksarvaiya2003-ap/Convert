import streamlit as st
from PIL import Image
import numpy as np
import cv2

st.title("Jacquard Texcell BMP Generator")

uploaded_file = st.file_uploader("Upload JPG Design", type=["jpg","jpeg","png"])

width = st.number_input("Width (Pixels)", min_value=10, value=200)
height = st.number_input("Height (Pixels)", min_value=10, value=200)

reed = st.number_input("Reed", value=100)
pick = st.number_input("Pick", value=100)

if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")
    image = image.resize((width, height))

    img = np.array(image)

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    _, thresh = cv2.threshold(gray,120,255,cv2.THRESH_BINARY_INV)

    kernel = np.ones((2,2),np.uint8)
    outline = cv2.dilate(thresh,kernel,iterations=1)

    result = np.zeros((height,width,3),dtype=np.uint8)

    # Blue background
    result[:,:] = [255,0,0]

    # Yellow figure
    result[thresh==255] = [0,255,255]

    # Red outline
    result[outline==255] = [0,0,255]

    bmp_image = Image.fromarray(result)

    st.image(bmp_image,caption="Preview")

    bmp_image.save("output.bmp")

    with open("output.bmp","rb") as f:
        st.download_button("Download BMP",f,"design.bmp")
