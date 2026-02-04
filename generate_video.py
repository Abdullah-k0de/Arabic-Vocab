import pandas as pd
from gtts import gTTS
import os
from moviepy import *
from bidi.algorithm import get_display
import arabic_reshaper
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Configuration
CSV_FILE = '3_words_utf.csv'
OUTPUT_VIDEO = 'vocab_output.mp4'
# Try to find a good Arabic font. 
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
BG_COLOR = (25, 25, 25) # Dark gray
TEXT_COLOR = (255, 255, 255)

def clean_filename(text):
    return "".join([c for c in text if c.isalpha() or c.isdigit() or c==' ']).rstrip()

def create_text_image(arabic_text, english_text, size=VIDEO_SIZE):
    # Create image with PIL
    img = Image.new('RGB', size, color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    try:
        font_ar = ImageFont.truetype(FONT_PATH, FONT_SIZE_AR)
        font_en = ImageFont.truetype(FONT_PATH, FONT_SIZE_EN)
    except IOError:
        print(f"Font not found at {FONT_PATH}, using default.")
        font_ar = ImageFont.load_default()
        font_en = ImageFont.load_default()

    # Process Arabic Text
    # 1. Reshape: Connects letters
    reshaped_text = arabic_reshaper.reshape(arabic_text)
    # 2. Bidi: Reorders for RTL display
    bidi_text = get_display(reshaped_text)
    
    # Calculate positions (Center)
    # PIL getbbox returns (left, top, right, bottom)
    bbox_ar = draw.textbbox((0, 0), bidi_text, font=font_ar)
    w_ar = bbox_ar[2] - bbox_ar[0]
    h_ar = bbox_ar[3] - bbox_ar[1]
    
    bbox_en = draw.textbbox((0, 0), english_text, font=font_en)
    w_en = bbox_en[2] - bbox_en[0]
    h_en = bbox_en[3] - bbox_en[1]
    
    x_ar = (size[0] - w_ar) / 2
    y_ar = (size[1] / 2) - h_ar - 20
    
    x_en = (size[0] - w_en) / 2
    y_en = (size[1] / 2) + 20
    
    draw.text((x_ar, y_ar), bidi_text, font=font_ar, fill=TEXT_COLOR)
    draw.text((x_en, y_en), english_text, font=font_en, fill=TEXT_COLOR)
    
    return np.array(img)

def generate_video():
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
            
            # 1. Generate Image
            img_array = create_text_image(arabic_word, english_meaning)
            image_clip = ImageClip(img_array)
            
            # 2. Generate Audio
            # Arabic Audio
            tts_ar = gTTS(arabic_word, lang='ar')
            ar_audio_path = f"temp_audio/ar_{index}.mp3"
            tts_ar.save(ar_audio_path)
            ar_audio = AudioFileClip(ar_audio_path)
            
            # English Audio
            tts_en = gTTS(english_meaning, lang='en')
            en_audio_path = f"temp_audio/en_{index}.mp3"
            tts_en.save(en_audio_path)
            en_audio = AudioFileClip(en_audio_path)
            
            # 3. Sequencing: Ar -> Pause -> En -> Pause
            # Pause is silence
            pause_duration = 0.5
            # Silence using AudioArrayClip
            samples = int(pause_duration * 44100)
            silence_array = np.zeros((samples, 2))
            silence = AudioArrayClip(silence_array, fps=44100)

            
            # Composite Audio
            # Note: concatenate_audioclips might be strictly typed in v2, check if list is fine.
            combined_audio = concatenate_audioclips([ar_audio, silence, en_audio, silence])
            
            # Set video clip duration to match audio (UPDATED FOR MOVIEPY V2)
            video_clip = image_clip.with_duration(combined_audio.duration)
            video_clip = video_clip.with_audio(combined_audio)
            
            clips.append(video_clip)
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            # print stack trace for debugging
            import traceback
            traceback.print_exc()
            continue
        
    if not clips:
        print("No clips generated.")
        return

    # Concatenate all clips
    final_video = concatenate_videoclips(clips)
    
    # Write output
    final_video.write_videofile(OUTPUT_VIDEO, fps=24)
    print(f"Video saved to {OUTPUT_VIDEO}")

if __name__ == "__main__":
    generate_video()
