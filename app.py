"""
JPG (line art) -> Jacquard/Texcelle red-outline BMP Converter
Traces the black lines of the source image and redraws them as a clean
red outline of an exact pixel width/height, on a plain background.
"""

import io
import numpy as np
import streamlit as st
from PIL import Image
from scipy.ndimage import binary_dilation
from skimage.morphology import skeletonize

# --------------------------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------------------------
st.set_page_config(page_title="JPG to Jacquard Outline BMP", page_icon="🧵", layout="wide")

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


def build_outline(
    image: Image.Image,
    width_px: int,
    height_px: int,
    outline_w: int,
    outline_h: int,
    invert: bool,
    outline_rgb: tuple,
    bg_rgb: tuple,
):
    """
    Detect the dark line-art in `image`, resize to (width_px, height_px), and
    redraw those lines at an EXACT pixel thickness of outline_w (horizontal)
    by outline_h (vertical) in the chosen outline colour on a plain background.
    Returns (index_arr, preview_image).
    """
    rgb_img = image.convert("RGB")

    # Work at a higher INTERNAL resolution first. Skeletonizing a very thin
    # line at the final small pixel size fragments it (breaks/gaps) and
    # makes curves look jagged. Doing skeleton+outline at a higher res, then
    # downscaling with high-quality resampling, keeps the line continuous
    # and the curves sharp and smooth.
    SCALE = 4
    MAX_INTERNAL = 1600
    scale = min(SCALE, max(1, MAX_INTERNAL // max(width_px, height_px)))
    internal_w, internal_h = width_px * scale, height_px * scale

    # High quality resize FIRST so curves stay smooth, then threshold.
    resized = rgb_img.resize((internal_w, internal_h), Image.LANCZOS)
    gray = np.array(resized.convert("L"))

    t = otsu_threshold(gray)
    mask = gray < t  # dark line pixels

    # The line-art is normally the smaller-area cluster; auto-correct if not.
    if mask.sum() > mask.size / 2:
        mask = ~mask
    if invert:
        mask = ~mask

    # Reduce the source line to a 1px centerline first, REGARDLESS of how
    # thick/blurry it is in the source JPG (JPEG compression, resizing, etc.
    # can make it 2-5px already). This guarantees the outline you draw next
    # ends up at EXACTLY outline_w x outline_h, never source_width + extra.
    skeleton = skeletonize(mask)

    # Grow the centerline to the EXACT requested thickness (scaled to the
    # internal resolution, corrected back down when we resize at the end).
    struct = np.ones((max(1, outline_h * scale), max(1, outline_w * scale)), dtype=bool)
    thick_line = binary_dilation(skeleton, structure=struct)

    # Downscale to the final requested size with high-quality resampling
    # (this acts like anti-aliasing / supersampling for smooth curves),
    # then re-threshold back to a clean 2-colour result.
    line_img = Image.fromarray((thick_line * 255).astype(np.uint8), mode="L")
    line_small = line_img.resize((width_px, height_px), Image.LANCZOS)
    final_mask = np.array(line_small) > 127

    # index array: 0 = background, 1 = outline
    index_arr = np.zeros((height_px, width_px), dtype=np.uint8)
    index_arr[final_mask] = 1

    preview_rgb = np.zeros((height_px, width_px, 3), dtype=np.uint8)
    preview_rgb[:, :] = bg_rgb
    preview_rgb[final_mask] = outline_rgb

    return index_arr, Image.fromarray(preview_rgb, "RGB")


def to_indexed_bmp_bytes(index_arr: np.ndarray, bg_rgb, outline_rgb) -> bytes:
    """Save the 2-colour index array as a true indexed-palette BMP."""
    pal_img = Image.fromarray(index_arr, mode="P")
    palette = [0] * 768
    for i, colour in enumerate((bg_rgb, outline_rgb)):
        palette[i * 3 : i * 3 + 3] = list(colour)
    pal_img.putpalette(palette)

    buf = io.BytesIO()
    pal_img.save(buf, format="BMP")
    return buf.getvalue()


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------
st.title("🧵 JPG → Red Outline BMP Converter")
st.caption("Upload line-art JPG/PNG and generate a clean red-outline BMP for Texcelle / Jacquard.")

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

    st.subheader("Outline thickness (exact pixels)")
    outline_w = st.number_input("Outline width (pixels)", min_value=1, max_value=50, value=2, step=1)
    outline_h = st.number_input("Outline height (pixels)", min_value=1, max_value=50, value=2, step=1)
    st.caption("The number you set here is the exact line thickness in the output.")

    st.subheader("Colours")
    outline_hex = st.color_picker("Outline colour", "#FF0000")
    bg_hex = st.color_picker("Background colour", "#FFFFFF")

    invert = st.checkbox("Invert line / background", value=False,
                          help="Tick this if the line-art and background come out swapped.")

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
        outline_rgb = hex_to_rgb(outline_hex)
        bg_rgb = hex_to_rgb(bg_hex)

        index_arr, preview_img = build_outline(
            src_image,
            int(width_px),
            int(height_px),
            int(outline_w),
            int(outline_h),
            invert,
            outline_rgb,
            bg_rgb,
        )

        with col2:
            st.subheader("Jacquard outline preview")
            st.image(preview_img, use_container_width=True)

        bmp_bytes = to_indexed_bmp_bytes(index_arr, bg_rgb, outline_rgb)
        st.success(f"Generated {width_px}x{height_px} px BMP (Reed {reed} / Pick {pick}).")
        st.download_button(
            label="⬇️ Download BMP",
            data=bmp_bytes,
            file_name="jacquard_outline.bmp",
            mime="image/bmp",
        )
else:
    st.info("Upload a JPG or PNG from the sidebar to get started.")
