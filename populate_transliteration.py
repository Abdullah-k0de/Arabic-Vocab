import pandas as pd
import os

def transliterate_arabic(text):
    # This is a specialized mapping for the vocabulary in Full.csv
    # It handles diacritics and common phonetic patterns.
    # Note: For 100% precision, a deep NLP library like camel-tools is needed,
    # but this covers the vocalized text in the dataset.
    
    mapping = {
        'أ': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h', 'خ': 'kh',
        'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's',
        'ض': 'd', 'ط': 't', 'ظ': 'z', 'ع': '‘', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
        'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y',
        'ة': 'ah', 'ء': '’', 'آ': 'ā', 'ى': 'ā', 'ؤ': 'u', 'ئ': 'i',
        'َ': 'a', 'ُ': 'u', 'ِ': 'i', 'ْ': '', 'ّ': '', 'ً': 'an', 'ٌ': 'un', 'ٍ': 'in'
    }
    
    parts = []
    # Simple split by backslash or forward slash as used in the CSV
    for word_part in text.split('\\'):
        word_part = word_part.strip()
        result = ""
        for i, char in enumerate(word_part):
            if char in mapping:
                # Handle Shadda (doubling the previous consonant)
                if char == 'ّ' and i > 0:
                    prev_char = word_part[i-1]
                    if prev_char in mapping:
                        result += mapping[prev_char]
                else:
                    result += mapping[char]
            else:
                result += char
        parts.append(result)
    
    return " / ".join(parts)

def main():
    input_file = 'datasets/Full.csv'
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print("Reading CSV...")
    df = pd.read_csv(input_file)
    
    # Drop empty rows (where Arabic is NaN)
    df = df.dropna(subset=['Arabic'])
    
    print(f"Propagating transliteration for {len(df)} rows...")
    df['Transliteration'] = df['Arabic'].apply(transliterate_arabic)
    
    # Save back
    df.to_csv(input_file, index=False, encoding='utf-8-sig')
    print(f"Successfully updated {input_file} with transliterations.")

if __name__ == "__main__":
    main()
