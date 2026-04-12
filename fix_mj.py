import re
with open('plugins/multijob.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('            else:\n            pass', '            else:\n                pass')

with open('plugins/multijob.py', 'w', encoding='utf-8') as f:
    f.write(text)
