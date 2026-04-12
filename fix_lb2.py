import re
with open('plugins/live_batch.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('                        pass\n            else:', '                        pass\n                except: pass\n            else:')

with open('plugins/live_batch.py', 'w', encoding='utf-8') as f:
    f.write(text)
