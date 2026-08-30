"""
JPG -> Jacquard/Texcelle BMP Converter
Converts a JPG motif into a 3-colour indexed BMP
(Figure = Yellow, Outline = Red, Ground = Blue)
suitable for Jacquard weaving pattern software (Texcelle).
"""

import io
import numpy as np
import streamlit as st
from PIL import Image
from scipy.ndimage import distance_transform_edt, label, maximum

# --------------------------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------------------------
st.set_page_config(page_title="JPG to Jacquard BMP", page_icon="🧵", layout="wide")

# --------------------------------------------------------------------------
# PASSWORD GATE
# --------------------------------------------------------------------------
# For security, set the password in Streamlit secrets (Settings -> Secrets on
# Streamlit Cloud) as:  APP_PASSWORD = "Dharmik@2026"
# If no secret is configured, this falls back to the default below so the
# app still works out of the box.
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "Dharmik@2026")


def check_password() -> bool:
    if st.session_state.get("authenticated", False):
        return True

    st.title("🔒 Login")
    pwd = st.text_input("Enter password", type="password")
    if st.button("Login"):
        if pwd == APP_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Wrong password. Try again.")
    return False


if not check_password():
    st.stop()

# --------------------------------------------------------------------------
# IMAGE PROCESSING
# --------------------------------------------------------------------------


def otsu_threshold(gray_arr: np.ndarray) -> int:
    """Compute the Otsu threshold of a grayscale array (0-255)."""
    hist, _ = np.histogram(gray_arr, bins=256, range=(0, 256))
    total = gray_arr.size
    sum_total = np.dot(np.arange(256), hist)
    sum_b, weight_b, max_var, threshold = 0.0, 0.0, 0.0, 0
    for i in range(256):
        weight_b += hist[i]
        if weight_b == 0:
            continue
        weight_f = total - weight_b
        if weight_f == 0:
            break
        sum_b += i * hist[i]
        mean_b = sum_b / weight_b
        mean_f = (sum_total - sum_b) / weight_f
        var_between = weight_b * weight_f * (mean_b - mean_f) ** 2
        if var_between > max_var:
            max_var = var_between
            threshold = i
    return threshold


def build_pattern(
    image: Image.Image,
    width_px: int,
    height_px: int,
    outline_w: int,
    outline_h: int,
    invert: bool,
    figure_rgb: tuple,
    outline_rgb: tuple,
    bg_rgb: tuple,
):
    """Convert a source image into a 3-colour (figure / outline / ground) index array."""
    rgb_img = image.convert("RGB")
    # High quality resize FIRST so curves stay smooth, then threshold.
    resized = rgb_img.resize((width_px, height_px), Image.LANCZOS)
    gray = np.array(resized.convert("L"))

    t = otsu_threshold(gray)
    mask = gray < t  # assume the darker cluster is the motif

    # The motif is usually the smaller-area cluster; auto-correct if not.
    if mask.sum() > mask.size / 2:
        mask = ~mask
    if invert:
        mask = ~mask

    # --- Adaptive outline band -------------------------------------------------
    # A fixed-size outline can completely swallow thin strokes (no fill left).
    # We cap the inward depth of the outline PER SHAPE so every connected
    # region always keeps at least a sliver of its own fill colour, no matter
    # how thick the requested outline is.
    t_in = max(1, (outline_w + outline_h) // 2 // 2)       # half-thickness, inward
    t_out = max(1, (outline_w + outline_h) // 2 - t_in)    # half-thickness, outward

    dist_in = distance_transform_edt(mask)
    dist_out = distance_transform_edt(~mask)

    labels_arr, n_labels = label(mask)
    if n_labels > 0:
        maxima = maximum(dist_in, labels=labels_arr, index=np.arange(1, n_labels + 1))
        cap_map = np.zeros_like(dist_in)
        cap_map[mask] = maxima[labels_arr[mask] - 1]
        effective_t_in = np.minimum(t_in, np.maximum(0, np.floor(cap_map) - 1))
    else:
        effective_t_in = np.zeros_like(dist_in)

    inside_band = mask & (dist_in <= effective_t_in)
    outside_band = (~mask) & (dist_out <= t_out)
    outline_ring = inside_band | outside_band
    fill = mask & ~inside_band

    # index array: 0 = background, 1 = figure, 2 = outline
    index_arr = np.zeros((height_px, width_px), dtype=np.uint8)
    index_arr[fill] = 1
    index_arr[outline_ring] = 2

    preview_rgb = np.zeros((height_px, width_px, 3), dtype=np.uint8)
    preview_rgb[:, :] = bg_rgb
    preview_rgb[index_arr == 1] = figure_rgb
    preview_rgb[index_arr == 2] = outline_rgb

    return index_arr, Image.fromarray(preview_rgb, "RGB")


def to_indexed_bmp_bytes(index_arr: np.ndarray, bg_rgb, figure_rgb, outline_rgb) -> bytes:
    """Save the 3-colour index array as a true indexed-palette BMP."""
    h, w = index_arr.shape
    pal_img = Image.fromarray(index_arr, mode="P")
    palette = [0] * 768
    for i, colour in enumerate((bg_rgb, figure_rgb, outline_rgb)):
        palette[i * 3 : i * 3 + 3] = list(colour)
    pal_img.putpalette(palette)

    buf = io.BytesIO()
    pal_img.save(buf, format="BMP")
    return buf.getvalue()


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------
st.title("🧵 JPG → Jacquard BMP Converter")
st.caption("Upload a motif JPG and generate a 3-colour BMP ready for Texcelle / Jacquard.")

with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Upload JPG / PNG", type=["jpg", "jpeg", "png"])

    st.subheader("Pattern size")
    width_px = st.number_input("Width (pixels)", min_value=10, max_value=2000, value=300, step=1)
    height_px = st.number_input("Height (pixels)", min_value=10, max_value=2000, value=300, step=1)

    st.subheader("Loom reference (label only)")
    reed = st.number_input("Reed", min_value=1, value=60, step=1)
    pick = st.number_input("Pick", min_value=1, value=60, step=1)
    st.caption("Reed/Pick are recorded for your reference — they do not change the pixel math yet.")

    st.subheader("Outline thickness")
    outline_w = st.number_input("Outline width (pixels)", min_value=1, max_value=50, value=3, step=1)
    outline_h = st.number_input("Outline height (pixels)", min_value=1, max_value=50, value=3, step=1)

    st.subheader("Colours")
    figure_hex = st.color_picker("Figure colour", "#FFFF00")
    outline_hex = st.color_picker("Outline colour", "#FF0000")
    bg_hex = st.color_picker("Ground colour", "#0000FF")

    invert = st.checkbox("Invert figure / background", value=False,
                          help="Tick this if the motif and background come out swapped.")

    process_btn = st.button("Generate BMP", type="primary")


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


if uploaded_file is not None:
    src_image = Image.open(uploaded_file)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original")
        st.image(src_image, use_container_width=True)

    if process_btn:
        figure_rgb = hex_to_rgb(figure_hex)
        outline_rgb = hex_to_rgb(outline_hex)
        bg_rgb = hex_to_rgb(bg_hex)

        index_arr, preview_img = build_pattern(
            src_image,
            int(width_px),
            int(height_px),
            int(outline_w),
            int(outline_h),
            invert,
            figure_rgb,
            outline_rgb,
            bg_rgb,
        )

        with col2:
            st.subheader("Jacquard pattern preview")
            st.image(preview_img, use_container_width=True)

        bmp_bytes = to_indexed_bmp_bytes(index_arr, bg_rgb, figure_rgb, outline_rgb)
        st.success(f"Generated {width_px}x{height_px} px BMP (Reed {reed} / Pick {pick}).")
        st.download_button(
            label="⬇️ Download BMP",
            data=bmp_bytes,
            file_name="jacquard_pattern.bmp",
            mime="image/bmp",
        )
else:
    st.info("Upload a JPG or PNG from the sidebar to get started.")
