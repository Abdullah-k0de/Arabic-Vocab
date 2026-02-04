import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display
from . import config

def clean_filename(text):
    return "".join([c for c in text if c.isalpha() or c.isdigit() or c==' ']).rstrip()

def get_random_background(size=config.VIDEO_SIZE):
    """Fetches a random image from Picsum."""
    url = f"https://picsum.photos/{size[0]}/{size[1]}"
    try:
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        return img
    except Exception as e:
        print(f"Failed to fetch background: {e}. Using dark color.")
        return Image.new('RGB', size, color=(25, 25, 25))

def create_text_image(arabic_text, english_text, background_img, size=config.VIDEO_SIZE):
    # Ensure background is RGBA for transparency operations
    img = background_img.convert("RGBA")
    
    # Initialize Draw (temp) to calculate text size for the box
    dummy_draw = ImageDraw.Draw(Image.new("RGB", (1,1)))
    
    try:
        font_ar = ImageFont.truetype(config.FONT_PATH, config.FONT_SIZE_AR)
        font_en = ImageFont.truetype(config.FONT_PATH, config.FONT_SIZE_EN)
    except IOError:
        print(f"Font not found at {config.FONT_PATH}, using default.")
        font_ar = ImageFont.load_default()
        font_en = ImageFont.load_default()

    # Process Arabic Text
    reshaped_text = arabic_reshaper.reshape(arabic_text)
    bidi_text = get_display(reshaped_text)
    
    # Calculate positions & Overlay Box
    bbox_ar = dummy_draw.textbbox((0, 0), bidi_text, font=font_ar)
    w_ar = bbox_ar[2] - bbox_ar[0]
    h_ar = bbox_ar[3] - bbox_ar[1]
    
    bbox_en = dummy_draw.textbbox((0, 0), english_text, font=font_en)
    w_en = bbox_en[2] - bbox_en[0]
    h_en = bbox_en[3] - bbox_en[1]
    
    # Vertical positions
    # Center the entire text block (Arabic + gap + English)
    gap = 40
    total_text_height = h_ar + gap + h_en
    
    start_y = (size[1] - total_text_height) / 2
    
    y_ar = start_y
    y_en = start_y + h_ar + gap
    
    x_ar = (size[0] - w_ar) / 2
    x_en = (size[0] - w_en) / 2
    
    # Create Box Overlay
    # Box width = Max width of text + padding
    padding_x = 60
    padding_y = 50
    box_w = max(w_ar, w_en) + (padding_x * 2)
    box_h = total_text_height + (padding_y * 2)
    
    # Box position (Centered)
    box_x1 = (size[0] - box_w) / 2
    box_y1 = start_y - padding_y
    box_x2 = box_x1 + box_w
    box_y2 = box_y1 + box_h
    
    # Draw Overlay
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # 1. Full Screen Light Overlay (for general contrast)
    overlay_draw.rectangle([0, 0, size[0], size[1]], fill=(0, 0, 0, 50)) # ~20% opacity
    
    # 2. Text Box Overlay (Darker for text readability)
    # Darker overlay for better contrast (opacity 180/255)
    overlay_draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(0, 0, 0, 180)) # ~70% opacity
    
    # Composite overlay onto background
    img = Image.alpha_composite(img, overlay)
    
    # Draw Text
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)
    
    draw.text((x_ar, y_ar), bidi_text, font=font_ar, fill=config.TEXT_COLOR)
    draw.text((x_en, y_en), english_text, font=font_en, fill=config.TEXT_COLOR)
    
    return np.array(img)
