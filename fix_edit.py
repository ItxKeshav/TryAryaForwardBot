import glob
import re

def fix_edit_text(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        
    orig = content
    
    # We will replace `await query.message.edit_text(`
    # with `await bot.send_message(query.message.chat.id, ` if query.message.photo else ...
    # We can write a tiny wrapper at the top of the file:
    wrapper = """
async def _safe_edit(bot, query, **kwargs):
    if getattr(query.message, 'photo', None):
        await query.message.delete()
        kwargs['chat_id'] = query.message.chat.id
        return await bot.send_message(**kwargs)
    else:
        return await query.message.edit_text(**kwargs)
"""
    if "async def _safe_edit" not in content and 'commands.py' in file_path:
        # insert wrapper after imports
        content = content.replace("async def _main_buttons", wrapper + "\nasync def _main_buttons")
        
        # Now replace `await query.message.edit_text(` with `await _safe_edit(bot, query, `
        # but only inside the callback handlers.
        content = re.sub(r'await\s+query\.message\.edit_text\(', r'await _safe_edit(bot, query, ', content)
        
    if orig != content:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"Fixed edit_text in {file_path}")

fix_edit_text("plugins/commands.py")
