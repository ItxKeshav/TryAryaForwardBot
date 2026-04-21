import requests
import urllib.parse
import os

def transliterate_to_hindi(text):
    if not text: return ""
    try:
        url = f"https://inputtools.google.com/request?text={urllib.parse.quote(text)}&itc=hi-t-i0-und&num=1&cp=0&cs=1&ie=utf-8&oe=utf-8&app=test"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        if data[0] == "SUCCESS":
            return data[1][0][1][0]
    except Exception:
        pass
    return text

def translate_to_hindi(text):
    if not text: return ""
    # 1. If already contains Devanagari, return as is
    if any('\u0900' <= c <= '\u097f' for c in text):
        return text
    
    # 2. Try regular translation first
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source='auto', target='hi').translate(text)
        
        # If translation returned the same string (often happens with Romanized Hindi)
        # We manually check if it was 'translated' or just returned input
        if translated.lower().strip() == text.lower().strip():
            return transliterate_to_hindi(text)
        
        return translated if translated else text
    except Exception:
        return transliterate_to_hindi(text)

output = []
output.append(f"Test 1 (The Warrior): {translate_to_hindi('The Warrior')}")
output.append(f"Test 2 (Tere Aane Se): {translate_to_hindi('Tere Aane Se')}")
output.append(f"Test 3 (Hindi Input): {translate_to_hindi('तेरे आने से')}")

with open("scratch/test_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))
print("Test completed. See scratch/test_out.txt")
