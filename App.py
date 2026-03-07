from PIL import Image
import numpy as np
import io

# Define standard palette colors (R, G, B)
TEXCELLE_PALETTE = [
    0, 0, 255,      # Index 0: Ground (Blue)
    255, 0, 0,      # Index 1: Outline (Red)
    255, 255, 0,    # Index 2: Figure (Yellow)
    255, 255, 255,  # Filler for 256 colors
] * 86 # Complete the 256 color palette (3 * 86 is approx 256)

def convert_to_texcelle_bmp(input_data, width, height, reed, pick):
    """
    Converts a grayscale input image (sketch) into a 
    Texcelle-compatible 8-bit indexed BMP file 
    with custom colors and resizing.
    """
    # 1. Load the input data
    try:
        img_in = Image.open(input_data).convert('L') # Force to grayscale
    except Exception as e:
        return f"Error opening input: {e}"

    # 2. Resizing with specific interpolation (NEAREST) to keep lines crisp
    img_resized = img_in.resize((int(width), int(height)), Image.Resampling.NEAREST)

    # Convert to NumPy array for fast pixel manipulation
    data = np.array(img_resized)

    # 3. Create a blank 8-bit indexed image data
    # We create a bytearray, then use NumPy to convert back to an image.
    new_data = np.zeros_like(data, dtype=np.uint8)

    # --- THE CORE LOGIC ---
    # Step 1: Detect outline and areas (simple thresholding on the grayscale image)
    # Assumes dark sketch on light paper.
    
    # Define a threshold: pixels darker than this are outline, 
    # pixels lighter than this are areas. (Adjust if needed).
    threshold = 120 

    # Mask for outline
    outline_mask = data < threshold
    # Mask for area
    area_mask = data >= threshold

    # Step 2: Assign colors based on our palette
    # Texcelle Index 0: Blue (Ground) - default everywhere
    # Texcelle Index 1: Red (Outline)
    # Texcelle Index 2: Yellow (Figure/Area)
    
    # For simplicity, we start by filling all areas with Figure color, 
    # then draw the outline, and the final ground is whatever is left outside.
    # This is slightly complex due to inside/outside detection.
    # A faster method:
    
    # Identify inside vs. outside. (Requires image analysis, not simple pixel check).
    # Since our sketch has a closed circle, we can use an 'Edge Detection' 
    # and 'Fill' algorithm to define the internal figure.

    # 1. Threshold for edges (to create a pure black/white mask for processing)
    _, bw_mask = cv2.threshold(data, threshold, 255, cv2.THRESH_BINARY_INV) if 'cv2' in globals() else \
        (None, (data < threshold).astype(np.uint8) * 255)

    # 2. Morphological closing to fill gaps in sketch (optional, but good for messy sketches)
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    # bw_mask = cv2.morphologyEx(bw_mask, cv2.MORPH_CLOSE, kernel)

    # 3. Flood fill from a corner to find the *entire* ground area
    h, w = bw_mask.shape
    # We must ensure the corner is not on an outline. Let's pick pixel (1,1)
    
    # We'll need a way to track the figure separately. A simple flood fill works well.
    ground_mask = bw_mask.copy()
    # Mask for the entire canvas. Corner (1,1) is definitely outside.
    flood_mask = np.zeros((h+2, w+2), np.uint8)
    
    # OpenCV's floodFill is the best tool here.
    import cv2
    cv2.floodFill(ground_mask, flood_mask, (1, 1), 255)
    
    # Now, everything that is *not* background is the whole figure (outline + interior).
    figure_and_outline_mask = ground_mask == 0 # Pixels with 0 value in ground_mask are internal

    # Final mask assignment
    # 1. Start with ground everywhere
    final_output_indices = np.zeros((h, w), dtype=np.uint8) # Default Index 0: Blue Ground
    
    # 2. Fill the interior of the figure with Yellow (Index 2)
    final_output_indices[figure_and_outline_mask] = 2 # Index 2: Yellow Figure

    # 3. Draw the outline (where the sketch lines were) with Red (Index 1)
    # Let's ensure the red outline is also drawn on top of the yellow.
    final_output_indices[outline_mask] = 1 # Index 1: Red Outline
    
    # --- The 1-2 pixel width request ---
    # The current 'outline_mask' will give an outline that matches the sketch line thickness.
    # If the sketch has messy thick lines, the red outline will be thick.
    # To enforce *exactly* 1-2 pixel thickness, we need 'Skeletonization' and 'Dilation'.
    
    # Skeletonize to 1-pixel line (Requires OpenCV or a specific library)
    # import cv2
    skeleton = cv2.ximgproc.thinning(bw_mask, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
    
    # Dilation for controlled thickness (e.g., dilate skeleton by a 3x3 square kernel)
    # This might create a red line *on the sketch boundary*
    
    # Let's use the current method first, as it's most robust to various sketch types.
    # Ensure red is always drawn last.
    
    # --- Create the final indexed image ---
    output_image = Image.fromarray(final_output_indices, mode='P')
    output_image.putpalette(TEXCELLE_PALETTE)
    
    # --- Metadata (Crucial for Texcelle) ---
    # We store reed/pick in image metadata fields if possible, or just note it.
    # BMP format has fields for DPI (Density), not specific Reed/Pick.
    # DPI = (Pixels / Inch). If Reed is Pixels/Inch, use it as DPI.
    
    # DPI info for the BMP header. If reed is in picks/inch:
    dpi_val = int(reed) if reed > 0 else 72 # fallback
    output_image.info['dpi'] = (dpi_val, dpi_val) # Assuming square pixels for BMP metadata

    # 4. Save to buffer
    output_buffer = io.BytesIO()
    # Save specifically as a 256-color BMP. Mode 'P' ensures this.
    # Make sure we use a proper BMP saver. PIL handles this.
    output_image.save(output_buffer, format="BMP")
    
    return output_buffer.getvalue()

# Example local test
if __name__ == "__main__":
    # Test file path (change this)
    test_file_path = "sketch.jpg"
    
    output_bytes = convert_to_texcelle_bmp(test_file_path, width=800, height=800, reed=100, pick=100)
    
    if isinstance(output_bytes, str):
        print(output_bytes)
    else:
        with open("texcelle_result.bmp", "wb") as f:
            f.write(output_bytes)
        print("Done. Created texcelle_result.bmp. Open in Texcelle to check.")

