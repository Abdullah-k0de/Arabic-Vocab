import asyncio
import edge_tts
import os
import shutil
from moviepy import *
import numpy as np

# List of Arabic Male Voices
VOICES = [
    ("ar-SA-HamedNeural", "Saudi Arabia"),
    ("ar-AE-HamdanNeural", "UAE"),
    ("ar-KW-FahedNeural", "Kuwait"),
    ("ar-MA-JamalNeural", "Morocco"),
    ("ar-DZ-IsmaelNeural", "Algeria"),
]

# Text with "Jeem" to test pronunciation (Camel, Beautiful, Mountain)
SAMPLE_TEXT = "السلام عليكم. أنا صوت من {}. حرف الجيم: جمل، جميل، جبل" 
# Translation: "Peace be upon you. I am a voice from {Country}. Letter Jeem: Jamal, Jamil, Jabal."

OUTPUT_FILE = "voice_samples.mp4"

async def generate_voice_sample(voice_id, country_name, index):
    text = SAMPLE_TEXT.format(country_name)
    audio_file = f"temp_voices/{voice_id}.mp3"
    
    # Generate Audio
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(audio_file)
    
    # Create Video Clip
    # White text on Black background
    # Using TextClip (requires ImageMagick) or ImageClip with PIL to avoid ImageMagick config issues on Windows if not set up.
    # Since we used PIL in the main script successfully, let's use that method here too for robustness.
    
    from PIL import Image, ImageDraw, ImageFont
    
    # Create simple image with Voice Name and Country
    img = Image.new('RGB', (1280, 720), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
        
    text_to_show = f"Voice: {voice_id}\nRegion: {country_name}"
    
    # Draw centered
    # bbox = draw.textbbox((0,0), text_to_show, font=font)
    # text_w = bbox[2] - bbox[0]
    # text_h = bbox[3] - bbox[1]
    # draw.text(((1280-text_w)/2, (720-text_h)/2), text_to_show, font=font, fill=(255, 255, 255), align="center")
    
    # Simplified center draw (approx)
    draw.text((100, 300), text_to_show, font=font, fill=(255, 255, 255))

    img_array = np.array(img)
    clip = ImageClip(img_array)
    
    audio = AudioFileClip(audio_file)
    clip = clip.with_duration(audio.duration + 0.5) # Add small pause
    clip = clip.with_audio(audio)
    
    return clip

async def main():
    if not os.path.exists("temp_voices"):
        os.makedirs("temp_voices")
        
    clips = []
    
    print("Generating samples...")
    for i, (voice_id, country) in enumerate(VOICES):
        print(f"Processing {voice_id} ({country})...")
        try:
            clip = await generate_voice_sample(voice_id, country, i)
            clips.append(clip)
        except Exception as e:
            print(f"Failed {voice_id}: {e}")
            
    if clips:
        final_video = concatenate_videoclips(clips)
        final_video.write_videofile(OUTPUT_FILE, fps=24)
        print(f"Done! Saved to {OUTPUT_FILE}")
    else:
        print("No clips generated.")

    # Cleanup temp_voices
    if os.path.exists('temp_voices'):
        print("Cleaning up temporary voice files...")
        shutil.rmtree('temp_voices')

if __name__ == "__main__":
    asyncio.run(main())
