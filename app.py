"""
Texcell Jacquard BMP Converter
------------------------------
Converts JPG line-art (sarees, motifs) into a 3-color 8-bit indexed BMP
ready for Texcell jacquard weaving software.

Palette (strict, in this index order):
    0 -> Blue   (0, 0, 255)   = Ground / background
    1 -> Yellow (255, 255, 0) = Figure / subject
    2 -> Red    (255, 0, 0)   = Outline (configurable thickness)

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import io
import hashlib
import numpy as np
import streamlit as st
from PIL import Image, ImageFilter
from scipy import ndimage

# ----------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Texcell Jacquard BMP Converter",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# Password gate
# ----------------------------------------------------------------------
# Note: a frontend password is NOT real security. Anyone with access to
# the Streamlit host or the source can read it. For a private tool this
# is acceptable as a soft gate.
PASSWORD = "DHARMIK@2003"
PASSWORD_HASH = hashlib.sha256(PASSWORD.encode()).hexdigest()


def check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.markdown(
        """
        <div style="text-align:center; padding-top:60px;">
            <h1 style="font-weight:700; letter-spacing:-1px;">🧵 Texcell Jacquard Studio</h1>
            <p style="color:#888; font-size:1.05rem;">Restricted access — please sign in to continue.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login", clear_on_submit=False):
            pwd = st.text_input("Password", type="password", placeholder="Enter access password")
            submitted = st.form_submit_button("Unlock", use_container_width=True)
            if submitted:
                if hashlib.sha256(pwd.encode()).hexdigest() == PASSWORD_HASH:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
    return False


# ----------------------------------------------------------------------
# Theme / styling
# ----------------------------------------------------------------------
def inject_css(dark: bool):
    if dark:
        bg, fg, card, border, muted = "#0b0f1a", "#f1f5f9", "#111827", "#1f2937", "#94a3b8"
    else:
        bg, fg, card, border, muted = "#fafbfc", "#0f172a", "#ffffff", "#e5e7eb", "#64748b"

    st.markdown(
        f"""
        <style>
            .stApp {{ background: {bg}; color: {fg}; }}
            section[data-testid="stSidebar"] {{ background: {card}; border-right: 1px solid {border}; }}
            h1, h2, h3, h4 {{ color: {fg}; letter-spacing: -0.5px; }}
            .metric-card {{
                background: {card};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 16px 18px;
                margin-bottom: 12px;
            }}
            .metric-card .label {{ color: {muted}; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }}
            .metric-card .value {{ color: {fg}; font-size: 1.4rem; font-weight: 600; margin-top: 4px; }}
            .stDownloadButton button, .stButton button {{
                border-radius: 10px; font-weight: 600;
            }}
            .swatch {{ display:inline-block; width:14px; height:14px; border-radius:3px; margin-right:8px; vertical-align:middle; border:1px solid {border}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# Image processing
# ----------------------------------------------------------------------
# Palette indices
IDX_GROUND = 0   # Blue
IDX_FIGURE = 1   # Yellow
IDX_OUTLINE = 2  # Red

PALETTE_RGB = [
    (0, 0, 255),     # 0 ground
    (255, 255, 0),   # 1 figure
    (255, 0, 0),     # 2 outline
]


def build_palette_bytes() -> bytes:
    """256-color palette padded with black; first 3 entries are our colors."""
    pal = []
    for r, g, b in PALETTE_RGB:
        pal.extend([r, g, b])
    pal.extend([0, 0, 0] * (256 - len(PALETTE_RGB)))
    return bytes(pal)


def process_image(
    pil_img: Image.Image,
    target_w: int,
    target_h: int,
    threshold: int,
    invert: bool,
    smoothing: int,
    outline_w: int,
    outline_h: int,
) -> Image.Image:
    """
    Returns a Pillow Image in mode 'P' (8-bit indexed) using our 3-color palette.
    """
    # 1. Resize to weaving dimensions (Reed x Pick == width x height in pixels)
    img = pil_img.convert("L").resize((target_w, target_h), Image.LANCZOS)

    # 2. Optional smoothing for cleaner curves before thresholding
    if smoothing > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=smoothing / 2.0))

    arr = np.array(img, dtype=np.uint8)

    # 3. Threshold -> binary figure mask
    if invert:
        figure_mask = arr >= threshold
    else:
        figure_mask = arr < threshold

    # 4. Clean tiny speckles (morphological opening)
    figure_mask = ndimage.binary_opening(figure_mask, iterations=1)

    # 5. Build outline using anisotropic dilation (separate W / H thickness)
    outline_mask = np.zeros_like(figure_mask, dtype=bool)
    if outline_w > 0 or outline_h > 0:
        # Horizontal dilation
        if outline_w > 0:
            kx = np.ones((1, 2 * outline_w + 1), dtype=bool)
            dil_x = ndimage.binary_dilation(figure_mask, structure=kx)
        else:
            dil_x = figure_mask
        # Vertical dilation
        if outline_h > 0:
            ky = np.ones((2 * outline_h + 1, 1), dtype=bool)
            dil_y = ndimage.binary_dilation(dil_x, structure=ky)
        else:
            dil_y = dil_x
        outline_mask = dil_y & ~figure_mask

    # 6. Compose indexed array
    indexed = np.full(figure_mask.shape, IDX_GROUND, dtype=np.uint8)
    indexed[outline_mask] = IDX_OUTLINE
    indexed[figure_mask] = IDX_FIGURE

    # 7. Wrap as Pillow 'P' image with our palette
    out = Image.fromarray(indexed, mode="P")
    out.putpalette(build_palette_bytes())
    return out


def to_bmp_bytes(indexed_img: Image.Image) -> bytes:
    buf = io.BytesIO()
    # Pillow writes 8-bit indexed BMP when mode='P'
    indexed_img.save(buf, format="BMP")
    return buf.getvalue()


# ----------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------
def main_app():
    # Theme toggle
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True

    with st.sidebar:
        st.markdown("### 🧵 Texcell Jacquard")
        st.caption("JPG → Indexed BMP for weaving")
        st.divider()

        st.session_state.dark_mode = st.toggle("🌙 Dark mode", value=st.session_state.dark_mode)

        st.markdown("#### 📐 Dimensions (pixels)")
        c1, c2 = st.columns(2)
        with c1:
            width = st.number_input("Width", min_value=16, max_value=8192, value=800, step=1)
        with c2:
            height = st.number_input("Height", min_value=16, max_value=8192, value=800, step=1)

        st.markdown("#### 🪡 Loom Settings")
        c3, c4 = st.columns(2)
        with c3:
            reed = st.number_input("Reed", min_value=1, max_value=500, value=80, step=1)
        with c4:
            pick = st.number_input("Pick", min_value=1, max_value=500, value=80, step=1)

        use_loom = st.checkbox("Derive size from Reed × Pick (per inch × inches)", value=False)
        if use_loom:
            inches_w = st.number_input("Cloth width (inches)", min_value=1.0, value=10.0, step=0.5)
            inches_h = st.number_input("Cloth height (inches)", min_value=1.0, value=10.0, step=0.5)
            width = int(reed * inches_w)
            height = int(pick * inches_h)
            st.info(f"Computed size: **{width} × {height} px**")

        st.markdown("#### ✏️ Outline Precision")
        outline_w = st.slider("Width outline (px)", 0, 20, 2)
        outline_h = st.slider("Height outline (px)", 0, 20, 2)

        st.markdown("#### 🎚️ Figure Detection")
        threshold = st.slider("Threshold (luminance)", 0, 255, 128)
        invert = st.checkbox("Invert (light = figure)", value=False)
        smoothing = st.slider("Curve smoothing", 0, 10, 2)

        st.divider()
        if st.button("🔒 Lock app", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    inject_css(st.session_state.dark_mode)

    # Header
    st.markdown("# Texcell Jacquard BMP Studio")
    st.caption("Convert JPG artwork into a pixel-perfect 3-color indexed BMP for jacquard weaving.")

    # Palette legend
    st.markdown(
        """
        <div style="margin: 8px 0 20px;">
            <span class="swatch" style="background:#FFFF00"></span> <b>Figure</b> (Yellow) &nbsp;&nbsp;
            <span class="swatch" style="background:#FF0000"></span> <b>Outline</b> (Red) &nbsp;&nbsp;
            <span class="swatch" style="background:#0000FF"></span> <b>Ground</b> (Blue)
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Drag & drop a JPG (or PNG) here",
        type=["jpg", "jpeg", "png", "bmp"],
        accept_multiple_files=False,
    )

    if not uploaded:
        st.info("⬆️ Upload an image to begin. Recommended: high-contrast line art.")
        return

    try:
        src = Image.open(uploaded)
    except Exception as e:
        st.error(f"Could not open image: {e}")
        return

    col_in, col_out = st.columns(2, gap="large")

    with col_in:
        st.markdown("#### Original")
        st.image(src, use_column_width=True)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="label">Source size</div>
                <div class="value">{src.width} × {src.height} px</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.spinner("Processing weave pattern..."):
        result = process_image(
            src,
            target_w=int(width),
            target_h=int(height),
            threshold=int(threshold),
            invert=invert,
            smoothing=int(smoothing),
            outline_w=int(outline_w),
            outline_h=int(outline_h),
        )

    with col_out:
        st.markdown("#### Converted preview (3-color indexed)")
        # Show as RGB for accurate browser rendering
        st.image(result.convert("RGB"), use_column_width=True)

        bmp_bytes = to_bmp_bytes(result)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="label">Output</div>
                <div class="value">{result.width} × {result.height} px · 8-bit indexed BMP · {len(bmp_bytes)/1024:.1f} KB</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            "⬇️ Download BMP for Texcell",
            data=bmp_bytes,
            file_name=f"jacquard_{result.width}x{result.height}.bmp",
            mime="image/bmp",
            use_container_width=True,
        )

    # Pixel composition stats
    arr = np.array(result)
    total = arr.size
    fig_pct = (arr == IDX_FIGURE).sum() / total * 100
    out_pct = (arr == IDX_OUTLINE).sum() / total * 100
    grd_pct = (arr == IDX_GROUND).sum() / total * 100

    st.divider()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Figure (Yellow)", f"{fig_pct:.1f}%")
    s2.metric("Outline (Red)", f"{out_pct:.1f}%")
    s3.metric("Ground (Blue)", f"{grd_pct:.1f}%")
    s4.metric("Reed × Pick", f"{reed} × {pick}")


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def run():
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    inject_css(st.session_state.dark_mode)
    if not check_password():
        return
    main_app()


if __name__ == "__main__":
    run()
