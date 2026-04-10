import pandas as pd
import os
import asyncio
import argparse
from moviepy import *
import numpy as np
import shutil
import src.config as config
import src.audio as audio
import src.graphics as graphics

async def process_batch(df_batch, batch_index, start_row, end_row, output_dir):
    clips = []
    
    # Separate temp dir for this batch
    batch_temp_audio = f"temp_audio_batch_{batch_index}"
    if not os.path.exists(batch_temp_audio):
        os.makedirs(batch_temp_audio)

    for index, row in df_batch.iterrows():
        try:
            arabic_word = str(row['Arabic'])
            english_meaning = str(row['English'])
            trans_text = str(row['Transliteration']) if 'Transliteration' in row else ""
            
            print(f"  [{batch_index}] Processing ({index+1}): {arabic_word}")
            
            bg_img = graphics.get_random_background()
            img_en_only = graphics.create_text_image(arabic_word, english_meaning, bg_img, show_arabic=False)
            img_full = graphics.create_text_image(arabic_word, english_meaning, bg_img, 
                                                 show_arabic=True, show_trans=True, trans_text=trans_text)
            
            # English Audio
            en_split_pattern = r",|;"
            en_audio = await audio.create_segmented_audio(
                english_meaning, config.VOICE_EN, en_split_pattern, config.PAUSE_EN_WORD, index, f"batch_{batch_index}_en"
            )
            
            # Arabic Audios
            ar_split_pattern = r"\\|/" 
            ar_audio_1 = await audio.create_segmented_audio(
                arabic_word, config.VOICE_AR, ar_split_pattern, config.PAUSE_AR_WORD, index, f"batch_{batch_index}_ar_n"
            )
            ar_audio_2 = await audio.create_segmented_audio(
                arabic_word, config.VOICE_AR, ar_split_pattern, config.PAUSE_AR_WORD, index, f"batch_{batch_index}_ar_s", rate=config.AR_REPETITION_RATE
            )
            ar_audio_3 = await audio.create_segmented_audio(
                arabic_word, config.VOICE_AR, ar_split_pattern, config.PAUSE_AR_WORD, index, f"batch_{batch_index}_ar_vs", rate=config.AR_REPETITION_RATE_SLOWEST
            )
            
            if not all([en_audio, ar_audio_1, ar_audio_2, ar_audio_3]):
                continue

            # Sequencing
            def get_silence(duration):
                samples = int(duration * 44100)
                if samples == 0: samples = 1
                return AudioArrayClip(np.zeros((samples, 2)), fps=44100)

            pause_after_en = get_silence(config.PAUSE_AFTER_ENGLISH)
            pause_between_ar = get_silence(config.PAUSE_BETWEEN_AR_REPEATS)
            lang_pause = get_silence(config.PAUSE_BETWEEN_LANGS)

            clip_en_audio = concatenate_audioclips([en_audio, pause_after_en])
            clip_en_video = ImageClip(img_en_only).with_duration(clip_en_audio.duration).with_audio(clip_en_audio)
            
            clip_ar_audio = concatenate_audioclips([
                ar_audio_1, pause_between_ar, 
                ar_audio_2, pause_between_ar, 
                ar_audio_3, lang_pause
            ])
            clip_ar_video = ImageClip(img_full).with_duration(clip_ar_audio.duration).with_audio(clip_ar_audio)
            
            video_clip = concatenate_videoclips([clip_en_video, clip_ar_video], method="compose")
            video_clip = video_clip.with_effects([vfx.FadeIn(0.75)])
            
            clips.append(video_clip)
        except Exception as e:
            print(f"Error in batch {batch_index}, row {index}: {e}")
            continue

    if clips:
        final_video = concatenate_videoclips(clips, method="compose")
        output_name = f"batch_{batch_index}_words_{start_row}_{end_row}.mp4"
        output_path = os.path.join(output_dir, output_name)
        final_video.write_videofile(output_path, fps=24)
        print(f"Batch {batch_index} Saved: {output_path}")

    # Cleanup temp audio for this row index range
    # (Actually the audio script handles temp_audio dir, 
    # but we should clean up after each batch to save space)
    if os.path.exists('temp_audio'):
        shutil.rmtree('temp_audio')
        os.makedirs('temp_audio')

async def main():
    parser = argparse.ArgumentParser(description="Generate vocabulary videos in batches.")
    parser.add_argument("--input", default=config.CSV_FILE, help="Path to input CSV file")
    parser.add_argument("--output-dir", default=config.OUTPUT_DIR, help="Directory to save generated videos")
    parser.add_argument("--batch-size", type=int, default=config.BATCH_SIZE, help="Number of words per video")
    
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: CSV file '{args.input}' not found.")
        return

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    try:
        df = pd.read_csv(args.input)
        df = df.dropna(subset=['Arabic']) # Ensure we only process rows with Arabic text
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    total_words = len(df)
    print(f"Starting batch processing for {total_words} words...")

    if not os.path.exists('temp_audio'):
        os.makedirs('temp_audio')

    # Calculate batches
    num_batches = (total_words + args.batch_size - 1) // args.batch_size

    for i in range(num_batches):
        start_idx = i * args.batch_size
        end_idx = min((i + 1) * args.batch_size, total_words)
        df_batch = df.iloc[start_idx:end_idx]
        
        # Human-readable range (1-indexed)
        start_row = start_idx + 1
        end_row = end_idx
        
        print(f"\n--- Processing Batch {i+1}/{num_batches} (Words {start_row}-{end_row}) ---")
        await process_batch(df_batch, i+1, start_row, end_row, args.output_dir)

    # Final Cleanup
    if os.path.exists('temp_audio'):
        shutil.rmtree('temp_audio')
    
    print("\nAll batches completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
