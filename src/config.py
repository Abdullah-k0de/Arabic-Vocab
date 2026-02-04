import os

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
