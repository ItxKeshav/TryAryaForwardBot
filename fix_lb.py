import re
with open('plugins/live_batch.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('                    except: pass\n\n            fetched = []', '                    except: pass\n                except: pass\n\n            fetched = []')

with open('plugins/live_batch.py', 'w', encoding='utf-8') as f:
    f.write(text)
