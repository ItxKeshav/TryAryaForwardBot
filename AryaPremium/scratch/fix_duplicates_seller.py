import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Update _show_story_profile for description localization
for i, line in enumerate(lines):
    if "desc = story.get(f'description_{lang}'" in line: # Already updated in previous step? Or did I miss it?
        pass # If already updated, skip.

# I'll do a fresh scan for all occurrences and fix them precisely.
for i in range(len(lines)):
    # Fix Story Profile description
    if "desc = story.get('description', '').strip()" in lines[i]:
        lines[i] = "    desc = story.get(f'description_{lang}', story.get('description', '')).strip()\n"
    
    # Fix My Stories (Command Handler) - Deduplication and Language logic
    if 'total = len(purchases)' in lines[i] and i < 1000:
        # We need to insert deduplication before this
        if 'seen = set()' not in lines[i-5:i]:
            lines.insert(i, "    # Deduplicate for UI\n    unique_p = []\n    seen = set()\n    for p in purchases:\n        p_id = str(p)\n        if p_id not in seen:\n            unique_p.append(p)\n            seen.add(p_id)\n    purchases = unique_p\n")
            # need to recalculate total
            # Find i again since we inserted lines
            for k in range(i, len(lines)):
                 if 'total = len(purchases)' in lines[k]:
                     # already there, total will be correct now
                     break

# I'll use a more robust replacement for the loop that builds My Stories keyboard
start_loop = -1
end_loop = -1
for i in range(len(lines)):
    if 'for pid in page_purchases:' in lines[i] and i < 1500: # Command handler one
        start_loop = i
        for j in range(i+1, len(lines)):
             if 'kb.append([InlineKeyboardButton(s_name, callback_data=f"mb#purchased_view_{pid}")])' in lines[j]:
                 end_loop = j + 1
                 break
        break

if start_loop != -1 and end_loop != -1:
    lines[start_loop:end_loop] = [r'''    for pid in page_purchases:
        try:
            st = await db.db.premium_stories.find_one({"_id": ObjectId(pid)})
            if st:
                en_name = st.get('story_name_en', 'Story')
                hi_name = st.get('story_name_hi', en_name)
                # Display only the relevant language name
                s_name = f"📖 {hi_name if lang == 'hi' else en_name}"
                kb.append([InlineKeyboardButton(s_name, callback_data=f"mb#purchased_view_{pid}")])
        except Exception: pass
''' + "\n"]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Deduplication and Language cleaning applied to command handler and profile.")
