import os
import re
import edge_tts
import numpy as np
from moviepy import AudioArrayClip, AudioFileClip, concatenate_audioclips

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
