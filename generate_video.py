import pandas as pd
import os
import asyncio
from moviepy import *
import numpy as np
import shutil
import src.config as config
import src.audio as audio
import src.graphics as graphics

async def main():
    if not os.path.exists(config.CSV_FILE):
        print(f"Error: CSV file '{config.CSV_FILE}' not found.")
        return

    # Load Data
    try:
        df = pd.read_csv(config.CSV_FILE)
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
            bg_img = graphics.get_random_background()
            
            # 1. Generate Image
            img_array = graphics.create_text_image(arabic_word, english_meaning, bg_img)
            image_clip = ImageClip(img_array)
            
            # 2. Generate Audio (Segmented)
            
            # Arabic: Split by backslash or forward slash
            ar_split_pattern = r"\\|/" 
            ar_audio = await audio.create_segmented_audio(
                arabic_word, config.VOICE_AR, ar_split_pattern, config.PAUSE_AR_WORD, index, "ar"
            )
            
            # English: Split by comma or semicolon
            en_split_pattern = r",|;"
            en_audio = await audio.create_segmented_audio(
                english_meaning, config.VOICE_EN, en_split_pattern, config.PAUSE_EN_WORD, index, "en"
            )
            
            if not ar_audio or not en_audio:
                print(f"Skipping row {index} due to audio failure")
                continue

            # 3. Sequencing: Ar_Composite -> Long Pause -> En_Composite -> Long Pause
            
            # Pause between languages
            lang_pause_samples = int(config.PAUSE_BETWEEN_LANGS * 44100)
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
        # Cleanup even if no clips (if temp_audio was created)
        if os.path.exists('temp_audio'):
            shutil.rmtree('temp_audio')
        return

    # Concatenate all clips
    final_video = concatenate_videoclips(clips, method="compose") 
    
    # Write output
    final_video.write_videofile(config.OUTPUT_VIDEO, fps=24)
    print(f"Video saved to {config.OUTPUT_VIDEO}")

    # Cleanup temp_audio
    if os.path.exists('temp_audio'):
        print("Cleaning up temporary audio files...")
        shutil.rmtree('temp_audio')

if __name__ == "__main__":
    asyncio.run(main())
