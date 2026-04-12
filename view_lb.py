lines = open('plugins/live_batch.py', encoding='utf-8').readlines()
for i in range(300, min(330, len(lines))):
    print(f'{i+1}: {lines[i]}', end='')
