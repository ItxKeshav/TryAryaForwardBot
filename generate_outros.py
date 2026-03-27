import os
import requests
from PIL import Image, ImageDraw, ImageFont

# Create directories
os.makedirs("assets", exist_ok=True)
os.makedirs("fonts", exist_ok=True)

import shutil

# To avoid 404/403 errors, trying to fall back to available Windows system fonts
# or simple PIL default font if needed.
# Since we need to generate images now, we will use Windows default Hindi and English fonts.
# The user wants "Tillana", "Yatra One", "Caveat", "Josefin Sans". 
# If they are installed on the OS they will be loaded, else we use Arial.
import glob
def get_font(name, fallback="arial.ttf"):
    # Trying to find font in windows
    paths = glob.glob(f"C:/Windows/Fonts/{name}*.ttf") + glob.glob(f"C:/Users/*/AppData/Local/Microsoft/Windows/Fonts/{name}*.ttf")
    if paths: return paths[0]
    return f"C:/Windows/Fonts/{fallback}"

font_hindi_t = get_font("Yatra", "Nirmala.ttf") # Nirmala UI supports Hindi
font_hindi_b = get_font("Tillana", "Nirmala.ttf")
font_eng_t = get_font("Josefin", "arialbd.ttf")
font_eng_b = get_font("Caveat", "arial.ttf")


def draw_text(draw, text, pos, font, fill=(255,255,255)):
    draw.text(pos, text, font=font, fill=fill)

W, H = 1920, 1080

def create_image(filename, lines, font_title, font_body):
    img = Image.new('RGB', (W, H), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    
    y = 150
    for i, (text, is_title, color) in enumerate(lines):
        font = font_title if is_title else font_body
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        x = (W - text_width) // 2
        draw_text(draw, text, (x, y), font, fill=color)
        y += 100 if is_title else 80
        if i == 0 or is_title:
            y += 30 # extra padding
            
    img.save(f"assets/{filename}")
    print(f"Saved {filename}")

# Image 1 (Hindi)
lines_1 = [
    ("नमस्ते! मैं आर्य बॉट हूँ।", True, (255, 200, 100)),
    ("आर्य बॉट के फायदे:", True, (100, 200, 255)),
    ("✅ बिना क्रम टूटे सभी एपिसोड्को को एक साथ जोड़ता है।", False, (255, 255, 255)),
    ("✅ उच्च गुणवत्ता (High Quality) की सुविधा।", False, (255, 255, 255)),
    ("", False, (0,0,0)),
    ("संभावित समस्याएं:", True, (255, 100, 100)),
    ("⚠️ कभी-कभी कोई एपिसोड आगे-पीछे हो सकता है (जैसे 11 पहले, 10 बाद में)।", False, (255, 255, 255)),
    ("⚠️ अगर कोई समस्या आए तो कृपया कमेंट करें, हम सुधारेंगे!", False, (255, 255, 255))
]

# Image 2 (Hindi)
lines_2 = [
    ("⚠️ कॉपीराइट चेतावनी:", True, (255, 100, 100)),
    ("इस चैनल पर कॉपीराइट स्ट्राइक आ सकती है।", False, (255, 255, 255)),
    ("हमसे जुड़े रहने और सभी कहानियों का अपडेट पाने के लिए", False, (255, 255, 255)),
    ("हमारा नया टेलीग्राम चैनल ज्वाइन करें:", False, (255, 255, 255)),
    ("👉 t.me/StoriesByJeetXNew", False, (100, 255, 100)),
    ("", False, (0,0,0)),
    ("💖 सपोर्ट (Support Us):", True, (255, 150, 255)),
    ("अगर हमारे काम से आपको मदद मिली हो,", False, (255, 255, 255)),
    ("तो कृपया डिस्क्रिप्शन बॉक्स में दिए गए Razorpay लिंक से", False, (255, 255, 255)),
    ("न्यूनतम 50 INR भेजकर मदद करें।", False, (255, 255, 255))
]

# Image 3 (English)
lines_3 = [
    ("Hello Strangers! I am Arya Bot.", True, (255, 200, 100)),
    ("Benefits of Arya Bot:", True, (100, 200, 255)),
    ("✨ Merges all episodes in exact order automatically.", False, (255, 255, 255)),
    ("✨ High quality processing seamlessly.", False, (255, 255, 255)),
    ("", False, (0,0,0)),
    ("Possible Issues:", True, (255, 100, 100)),
    ("📉 Minor issues like episode order mismatches may occur.", False, (255, 255, 255)),
    ("💡 Please drop a comment if you face major issues contextually!", False, (255, 255, 255)),
    ("We will try to fix/improve them rapidly.", False, (255, 255, 255))
]

# Image 4 (English)
lines_4 = [
    ("⚠️ COPYRIGHT WARNING:", True, (255, 100, 100)),
    ("Copyright issues may strike at any time.", False, (255, 255, 255)),
    ("Join my Telegram channel to never miss an update or new story!", False, (255, 255, 255)),
    ("🔗 t.me/StoriesByJeetXNew", False, (100, 255, 100)),
    ("", False, (0,0,0)),
    ("💖 SUPPORT REQUEST:", True, (255, 150, 255)),
    ("If my work helped you in any way, please support me!", False, (255, 255, 255)),
    ("Find the Razorpay payment link in the description (minimum 50 INR).", False, (255, 255, 255)),
    ("This keeps the flow of stories alive!", False, (255, 255, 255))
]

try:
    fh_t = ImageFont.load_default()
    fh_b = ImageFont.load_default()
    fe_t = ImageFont.load_default()
    fe_b = ImageFont.load_default()
    
    # Try loading custom fonts if exists
    try: fh_t = ImageFont.truetype(font_hindi_t, 60)
    except: pass
    try: fh_b = ImageFont.truetype(font_hindi_b, 50)
    except: pass
    try: fe_t = ImageFont.truetype(font_eng_t, 65)
    except: pass
    try: fe_b = ImageFont.truetype(font_eng_b, 75)
    except: pass

    create_image("outro_1.jpg", lines_1, fh_t, fh_b)
    create_image("outro_2.jpg", lines_2, fh_t, fh_b)
    create_image("outro_3.jpg", lines_3, fe_t, fe_b)
    create_image("outro_4.jpg", lines_4, fe_t, fe_b)
except Exception as e:
    print(e)
