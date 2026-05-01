import re
import unicodedata

def clean_filename_for_telegram(title):
    nfkc = unicodedata.normalize('NFKC', title)
    ascii_only = nfkc.encode('ascii', 'ignore').decode('ascii')
    safe = re.sub(r'[^a-zA-Z0-9\s\-&]', '', ascii_only)
    safe = re.sub(r'\s+', ' ', safe).strip()
    return safe

print(clean_filename_for_telegram("762-763 - 𝑇ℎ𝑒 𝑅𝑒𝑡𝑢𝑟𝑛 𝐵𝑦 𝐴𝑟𝑦𝑎"))
print(clean_filename_for_telegram("( 10-11 - The Leader )"))
