lines = open('plugins/taskjob.py', encoding='utf-8').readlines()
for i in range(618, min(630, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')
