import re

files_changes = {
    'plugins/cleaner.py': [
        ('                if _sh.which("cpulimit"):\n                    cmd_run = ["cpulimit", "-l", str(CL_FFMPEG_CPU_LIMIT), "-f", "--"] + cmd\n                else:\n                    cmd_run = cmd', '                cmd_run = cmd')
    ],
    'plugins/merger.py': [
        ('                    # Prefer cpulimit wrapper (hard CPU cap) if installed on VPS\n                    if _sh.which("cpulimit"):\n                        actual_cmd = ["cpulimit", "-l", str(FFMPEG_CPU_LIMIT), "-f", "--"] + cmd_list\n                    else:\n                        actual_cmd = cmd_list', '                    actual_cmd = cmd_list')
    ]
}

for fp, replaces in files_changes.items():
    with open(fp, 'r', encoding='utf-8') as f:
        data = f.read()
    
    for old, new in replaces:
        data = data.replace(old, new)
        
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(data)
    print(f'Processed {fp}')
