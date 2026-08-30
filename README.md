# Jacquard BMP Studio

Private Streamlit app to convert JPG design images into 3-color BMP files for Jacquard / Texcell saree weaving.

**Colors fixed:** Figure = Yellow | Outline = Red | Ground = Blue

## Usage

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features
- Password protected (Dharmik@2026)
- Upload JPG / PNG
- Auto-convert to BMP (24-bit)
- Sharp smooth curves via bilateral smoothing + contour averaging
- Custom Width / Height (pixels)
- Reed & Pick recording for weave specs
- Outline width / height control
- Download BMP instantly

## Deploy to GitHub / Streamlit Cloud
1. Push `app.py` + `requirements.txt` to a GitHub repo
2. Connect repo to Streamlit Community Cloud
3. Set `pythonVersion` if needed — works out of the box
