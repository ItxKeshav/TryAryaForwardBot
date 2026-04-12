import re
with open('plugins/multijob.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_func_regex = re.compile(r'async def _mj_ensure_client_alive\(client\):.*?raise RuntimeError\("MULTIJOB_RECONNECT_FAILED: client failed to reconnect after 3 attempts"\)', re.DOTALL)

new_func = '''async def _mj_ensure_client_alive(client):
    try:
        if not getattr(client, "is_connected", True):
            await client.connect()
    except Exception as e:
        pass
    return client'''

text = old_func_regex.sub(new_func, text)

with open('plugins/multijob.py', 'w', encoding='utf-8') as f:
    f.write(text)
