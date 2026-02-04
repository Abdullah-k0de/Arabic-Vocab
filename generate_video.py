import pandas as pd
import os
import asyncio
import edge_tts
from moviepy import *
import requests
from io import BytesIO
from bidi.algorithm import get_display
import arabic_reshaper
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import re

# Configuration
CSV_FILE = 'datasets/3_words_utf.csv'
OUTPUT_VIDEO = 'vocab_output.mp4'

# Voice Configuration (Male Voices)
VOICE_AR = "ar-MA-JamalNeural" # Arabic Male (Morocco - Standard Jeem)
VOICE_EN = "en-US-ChristopherNeural" # English Male

# Pause Configuration (Seconds)
PAUSE_AR_WORD = 1.0       # Pause between Arabic parts (separated by \)
PAUSE_EN_WORD = 0.5       # Pause between English parts (separated by , or ;)
PAUSE_BETWEEN_LANGS = 1.5 # Pause between Arabic block and English block

# Font setup
font_candidates = [
    'C:\\Windows\\Fonts\\arial.ttf',
    'C:\\Windows\\Fonts\\segoeui.ttf',
    'C:\\Windows\\Fonts\\tahoma.ttf',
    'C:\\Windows\\Fonts\\micross.ttf'
]
FONT_PATH = 'arial.ttf' # Fallback
for f in font_candidates:
    if os.path.exists(f):
        FONT_PATH = f
        break

FONT_SIZE_AR = 80
FONT_SIZE_EN = 50
VIDEO_SIZE = (1280, 720)
TEXT_COLOR = (255, 255, 255)

def clean_filename(text):
    return "".join([c for c in text if c.isalpha() or c.isdigit() or c==' ']).rstrip()

def get_random_background(size=VIDEO_SIZE):
    """Fetches a random image from Picsum."""
    url = f"https://picsum.photos/{size[0]}/{size[1]}"
    try:
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        return img
    except Exception as e:
        print(f"Failed to fetch background: {e}. Using dark color.")
        return Image.new('RGB', size, color=(25, 25, 25))

def create_text_image(arabic_text, english_text, background_img, size=VIDEO_SIZE):
    # Ensure background is RGBA for transparency operations
    img = background_img.convert("RGBA")
    
    # Initialize Draw (temp) to calculate text size for the box
    dummy_draw = ImageDraw.Draw(Image.new("RGB", (1,1)))
    
    try:
        font_ar = ImageFont.truetype(FONT_PATH, FONT_SIZE_AR)
        font_en = ImageFont.truetype(FONT_PATH, FONT_SIZE_EN)
    except IOError:
        print(f"Font not found at {FONT_PATH}, using default.")
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
    # Darker overlay for better contrast (opacity 180/255)
    overlay_draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(0, 0, 0, 180))
    
    # Composite overlay onto background
    img = Image.alpha_composite(img, overlay)
    
    # Draw Text
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)
    
    draw.text((x_ar, y_ar), bidi_text, font=font_ar, fill=TEXT_COLOR)
    draw.text((x_en, y_en), english_text, font=font_en, fill=TEXT_COLOR)
    
    return np.array(img)

async def generate_single_audio_file(text, voice, output_path):
    """Generates a single TTS file using EdgeTTS."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

async def create_segmented_audio(full_text, voice, separators, pause_duration, row_index, lang_prefix):
    """
    Splits text by separators, generates audio for each part, 
    and returns a concatenated AudioFileClip with updated pauses.
    """
    # Create temp dir
    temp_dir = f"temp_audio/{row_index}_{lang_prefix}"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Split text (regex split by separators, keeping only non-empty parts)
    # separators is a string of chars e.g. r"\\|/" or r",|;"
    parts = re.split(separators, full_text)
    # Clean parts
    parts = [p.strip() for p in parts if p.strip()]
    
    audio_clips = []
    
    # Silence clip
    silence_samples = int(pause_duration * 44100)
    # Ensure at least 1 sample to avoid errors if pause is 0
    if silence_samples == 0: silence_samples = 1
    silence_array = np.zeros((silence_samples, 2))
    silence_clip = AudioArrayClip(silence_array, fps=44100)
    
    for i, part in enumerate(parts):
        print(f"    Generating part {i+1}/{len(parts)}: '{part}'")
        output_path = f"{temp_dir}/part_{i}.mp3"
        
        try:
            await generate_single_audio_file(part, voice, output_path)
            clip = AudioFileClip(output_path)
            audio_clips.append(clip)
            
            # Add pause if not last item
            if i < len(parts) - 1:
                audio_clips.append(silence_clip)
        except Exception as e:
            print(f"    Error generating audio for part '{part}': {e}")
            
    if not audio_clips:
        return None
        
    return concatenate_audioclips(audio_clips)

async def main():
    if not os.path.exists(CSV_FILE):
        print(f"Error: CSV file '{CSV_FILE}' not found.")
        return

    # Load Data
    try:
        df = pd.read_csv(CSV_FILE)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    clips = []
    
    if not os.path.exists('temp_audio'):
        os.makedirs('temp_audio')

    for index, row in df.iterrows():
        try:
            arabic_word = str(row['Arabic'])
            english_meaning = str(row['English'])
            
            print(f"Processing ({index+1}/{len(df)}): {arabic_word} - {english_meaning}")
            
            # 0. Get Background
            bg_img = get_random_background()
            
            # 1. Generate Image
            img_array = create_text_image(arabic_word, english_meaning, bg_img)
            image_clip = ImageClip(img_array)
            
            # 2. Generate Audio (Segmented)
            
            # Arabic: Split by backslash or forward slash
            ar_split_pattern = r"\\|/" 
            ar_audio = await create_segmented_audio(
                arabic_word, VOICE_AR, ar_split_pattern, PAUSE_AR_WORD, index, "ar"
            )
            
            # English: Split by comma or semicolon
            en_split_pattern = r",|;"
            en_audio = await create_segmented_audio(
                english_meaning, VOICE_EN, en_split_pattern, PAUSE_EN_WORD, index, "en"
            )
            
            if not ar_audio or not en_audio:
                print(f"Skipping row {index} due to audio failure")
                continue

            # 3. Sequencing: Ar_Composite -> Long Pause -> En_Composite -> Long Pause
            
            # Pause between languages
            lang_pause_samples = int(PAUSE_BETWEEN_LANGS * 44100)
            if lang_pause_samples == 0: lang_pause_samples = 1
            lang_pause = AudioArrayClip(np.zeros((lang_pause_samples, 2)), fps=44100)

            # Composite Audio
            combined_audio = concatenate_audioclips([ar_audio, lang_pause, en_audio, lang_pause])
            
            # Set video clip duration
            video_clip = image_clip.with_duration(combined_audio.duration)
            video_clip = video_clip.with_audio(combined_audio)
            
            # Add Fade Transition
            video_clip = video_clip.with_effects([vfx.FadeIn(0.75)])
            
            clips.append(video_clip)
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            import traceback
            traceback.print_exc()
            continue
        
    if not clips:
        print("No clips generated.")
        return

    # Concatenate all clips
    final_video = concatenate_videoclips(clips, method="compose") 
    
    # Write output
    final_video.write_videofile(OUTPUT_VIDEO, fps=24)
    print(f"Video saved to {OUTPUT_VIDEO}")

if __name__ == "__main__":
    asyncio.run(main())
