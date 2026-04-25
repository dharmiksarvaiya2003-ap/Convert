# Texcell Jacquard BMP Studio

A private Streamlit app that converts JPG artwork into a **3-color 8-bit indexed BMP** ready for **Texcell** jacquard weaving software.

## 🎨 Color mapping (strict)

| Index | Color  | RGB           | Role            |
|-------|--------|---------------|-----------------|
| 0     | Blue   | (0, 0, 255)   | Ground / bg     |
| 1     | Yellow | (255, 255, 0) | Figure / subject|
| 2     | Red    | (255, 0, 0)   | Outline         |

## 🔐 Access

Password gate on launch. Default password: `DHARMIK@2003`
(Change `PASSWORD` constant at the top of `app.py`.)

> ⚠️ A frontend password is a soft gate, not real security. The hash is in
> the source. For real privacy, deploy on a private host or behind SSO.

## 🚀 Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

## ☁️ Deploy on Streamlit Community Cloud

1. Push this folder to a **GitHub repo** (public or private).
2. Go to https://share.streamlit.io and click **New app**.
3. Pick the repo, branch, and `app.py` as the entry point.
4. Deploy.

## 🧰 Features

- 🔒 Password-protected gate (SHA-256 hashed)
- 🌙 Dark / light theme toggle
- 📤 Drag-and-drop JPG/PNG/BMP upload
- 📐 Custom width / height in pixels
- 🪡 Reed & Pick inputs (optional auto-sizing from cloth dimensions)
- ✏️ Independent **Width** and **Height** outline thickness sliders
- 🎚️ Adjustable luminance threshold + invert
- 🌀 Curve smoothing (Gaussian) for clean weave-ready edges
- 🧹 Morphological denoise to remove specks
- 👀 Real-time preview of the converted BMP
- ⬇️ One-click download of the indexed BMP for Texcell

## 📁 Repo layout

```
texcell-jacquard/
├── app.py
├── requirements.txt
└── README.md
```

## 🛠️ How the conversion works

1. Resize the source to target weaving dimensions (Lanczos).
2. Convert to grayscale and apply optional Gaussian smoothing.
3. Threshold to a binary **figure mask** (with optional invert).
4. Morphological opening removes speckle noise.
5. Anisotropic dilation (separate W/H) builds the **outline ring**
   around the figure — the outline is the dilated area minus the figure.
6. Compose an indexed array: 0 ground, 1 figure, 2 outline.
7. Save as Pillow `mode="P"` BMP → standard 8-bit indexed BMP that
   Texcell reads natively.
