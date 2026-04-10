# Arabic Vocabulary Video Generator

This project generates educational videos for Arabic vocabulary words using Python. It combines text-to-speech (TTS) audio, dynamic text overlays, and background images to create engaging video clips.

## Features

- **Batch Processing**: Split large datasets (e.g., 700+ words) into multiple videos automatically.
- **Transliteration Support**: Automated phonetic transliteration tool included.
- **High-Quality TTS**: Triple repetition sequence (Normal -> Slow -> Very Slow) for better learning.
- **Dynamic Visuals**: English at the top, Arabic in the middle, and Transliteration at the bottom.
- **CLI Arguments**: Fully customizable input/output paths via the terminal.

## Prerequisites

- Python 3.8+
- [ImageMagick](https://imagemagick.org/script/download.php) (Recommended for MoviePy)

### Dependencies

```bash
pip install pandas moviepy edge-tts requests python-bidi arabic-reshaper Pillow numpy
```

## Project Structure

```
Arabic_Vocab/
├── datasets/
│   ├── Full.csv              # Main dataset (Arabic, English)
│   └── 3_words_utf.csv       # Small test dataset
├── src/
│   ├── config.py             # Configuration (Voices, Pauses, Fonts)
│   ├── audio.py              # Audio generation logic
│   └── graphics.py           # Image and text rendering
├── populate_transliteration.py # Tool to add phonetics to your CSV
├── generate_video.py         # Main batch generator script
└── README.md
```

## Usage

### 1. Prepare Your Data
Ensure your CSV file has `Arabic` and `English` columns. If you don't have transliterations yet, run the included tool:

```bash
python populate_transliteration.py
```
*(Default: updates `datasets/Full.csv`. Modify the script if using a different file.)*

### 2. Run the Batch Generator
Generate videos in chunks (e.g., 100 words per video):

```bash
python generate_video.py --input datasets/Full.csv --output-dir outputs --batch-size 100
```

The script will:
- Partition the words into batches.
- Create videos named like `batch_1_words_1_100.mp4`.
- Sequence each word: **English** -> **Pause** -> **Arabic** -> **Arabic (Slow)** -> **Arabic (Very Slow)**.

## Configuration

Customize settings in `src/config.py`:
- **Triple Repetition**: Adjust `AR_REPETITION_RATE` and `AR_REPETITION_RATE_SLOWEST`.
- **Layout**: The system uses a 3-line centered layout (English, Arabic, Transliteration).
- **Voices**: Change `VOICE_AR` or `VOICE_EN` for different accents.
