
file_path = r'c:\Users\User\Downloads\AryaBotNew\TryAryaBot\AryaPremium\plugins\mgmt\market_mgmt.py'
append_path = r'c:\Users\User\Downloads\AryaBotNew\TryAryaBot\AryaPremium\scratch\broadcast_func.txt'

with open(append_path, 'r', encoding='utf-8') as f:
    code_to_append = f.read()

with open(file_path, 'a', encoding='utf-8') as f:
    f.write("\n" + code_to_append)

print("Broadcast function appended successfully.")
