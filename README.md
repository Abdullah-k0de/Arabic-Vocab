# Arabic Vocabulary Video Generator

This project generates educational videos for Arabic vocabulary words using Python. It combines text-to-speech (TTS) audio, dynamic text overlays, and background images to create engaging video clips.

## Features

- **Automated Video Generation**: Converts a CSV list of Arabic and English words into a video.
- **High-Quality TTS**: Uses Microsoft Edge TTS for natural-sounding Arabic and English voices.
- **Smart Pause Handling**: Automatically inserts pauses between words and language segments for better learning pacing.
- **Dynamic Visuals**: Fetches random background images and overlays text with proper Arabic support (reshaping and bidi).
- **Modular Design**: Code is organized into `src` modules for easier maintenance.
- **Auto-Cleanup**: Temporary files (`temp_audio`, `temp_voices`) are automatically cleaned up after generation.

## Prerequisites

- Python 3.8+
- [ImageMagick](https://imagemagick.org/script/download.php) (Required by MoviePy for some operations, though this project uses PIL for text primarily, having it installed is recommended).

### Dependencies

Install the required Python packages:

```bash
pip install pandas moviepy edge-tts requests python-bidi arabic-reshaper Pillow numpy
```

## Project Structure

```
Arabic_Vocab/
├── datasets/
│   └── 3_words_utf.csv       # Input data (Arabic, English columns)
├── src/
│   ├── config.py             # Configuration (Voices, Pauses, Fonts)
│   ├── audio.py              # Audio generation logic
│   └── graphics.py           # Image and text rendering
├── voices/
│   └── test_voices.py        # Utility to test different TTS voices
├── generate_video.py         # Main script to run
└── README.md
```

## Usage

1.  **Prepare Data**: Ensure your CSV file is at `datasets/3_words_utf.csv` (or update `src/config.py`). It should have columns `Arabic` and `English`.
2.  **Run the Generator**:

    ```bash
    python generate_video.py
    ```

    The script will:
    - distinct audio segments for each word.
    - Fetch background images.
    - Compose the video clips.
    - Save the final output to `vocab_output.mp4`.

## Testing Voices

To hear samples of different Arabic voices (Saudi, UAE, Kuwait, Morocco, Algeria):

```bash
python voices/test_voices.py
```

This will generate `voice_samples.mp4` showcasing the available voices.

## Configuration

You can customize the following in `src/config.py`:
- **Voices**: Change `VOICE_AR` or `VOICE_EN` to different Edge TTS voice IDs.
- **Pauses**: Adjust `PAUSE_AR_WORD`, `PAUSE_EN_WORD`, etc.
- **Fonts**: Add paths to your preferred fonts in `font_candidates`.
