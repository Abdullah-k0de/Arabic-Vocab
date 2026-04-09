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
            trans_text = str(row['Transliteration']) if 'Transliteration' in row else ""
            
            print(f"Processing ({index+1}/{len(df)}): {arabic_word} - {english_meaning}")
            
            # 0. Get Background
            bg_img = graphics.get_random_background()
            
            # 1. Generate Images
            # Part 1: English Only
            img_en_only = graphics.create_text_image(arabic_word, english_meaning, bg_img, show_arabic=False)
            # Part 2: English + Arabic + Transliteration
            img_full = graphics.create_text_image(arabic_word, english_meaning, bg_img, 
                                                 show_arabic=True, show_trans=True, trans_text=trans_text)
            
            # 2. Generate Audio (Segmented)
            
            # English
            en_split_pattern = r",|;"
            en_audio = await audio.create_segmented_audio(
                english_meaning, config.VOICE_EN, en_split_pattern, config.PAUSE_EN_WORD, index, "en"
            )
            
            # Arabic 1 (Normal)
            ar_split_pattern = r"\\|/" 
            ar_audio_1 = await audio.create_segmented_audio(
                arabic_word, config.VOICE_AR, ar_split_pattern, config.PAUSE_AR_WORD, index, "ar_norm"
            )
            
            # Arabic 2 (Slow)
            ar_audio_2 = await audio.create_segmented_audio(
                arabic_word, config.VOICE_AR, ar_split_pattern, config.PAUSE_AR_WORD, index, "ar_slow", rate=config.AR_REPETITION_RATE
            )

            # Arabic 3 (Slowest)
            ar_audio_3 = await audio.create_segmented_audio(
                arabic_word, config.VOICE_AR, ar_split_pattern, config.PAUSE_AR_WORD, index, "ar_slowest", rate=config.AR_REPETITION_RATE_SLOWEST
            )
            
            if not all([en_audio, ar_audio_1, ar_audio_2, ar_audio_3]):
                print(f"Skipping row {index} due to audio failure")
                continue

            # 3. Sequencing
            
            # Helper for silence
            def get_silence(duration):
                samples = int(duration * 44100)
                if samples == 0: samples = 1
                return AudioArrayClip(np.zeros((samples, 2)), fps=44100)

            pause_after_en = get_silence(config.PAUSE_AFTER_ENGLISH)
            pause_between_ar = get_silence(config.PAUSE_BETWEEN_AR_REPEATS)
            lang_pause = get_silence(config.PAUSE_BETWEEN_LANGS)

            # Part 1: English + 2s Pause (Visual: English Only)
            clip_en_audio = concatenate_audioclips([en_audio, pause_after_en])
            clip_en_video = ImageClip(img_en_only).with_duration(clip_en_audio.duration).with_audio(clip_en_audio)
            
            # Part 2: Arabic Repetitions (Visual: Full)
            # Normal -> Slow -> Slowest
            clip_ar_audio = concatenate_audioclips([
                ar_audio_1, pause_between_ar, 
                ar_audio_2, pause_between_ar, 
                ar_audio_3, lang_pause
            ])
            clip_ar_video = ImageClip(img_full).with_duration(clip_ar_audio.duration).with_audio(clip_ar_audio)
            
            # Combine & Transition
            video_clip = concatenate_videoclips([clip_en_video, clip_ar_video], method="compose")
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
