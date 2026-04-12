import re
with open('plugins/taskjob.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('        _pause_events.pop(job_id, None)\n            pass', '        _pause_events.pop(job_id, None)')

with open('plugins/taskjob.py', 'w', encoding='utf-8') as f:
    f.write(text)
