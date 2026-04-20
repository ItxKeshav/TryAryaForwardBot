import os
import re

file_path = r'c:\Users\User\Downloads\AryaBotNew\TryAryaBot\AryaPremium\plugins\userbot\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

def clean_duplicates(lines):
    new_lines = []
    seen_tc_text = False
    seen_refund_text = False
    seen_show_tc = False
    
    # We want to keep the first occurrence of _get_tc_text, _get_refund_text, _show_tc
    # But specifically, we want to keep the ones at the TOP (lines 200-300 range approx)
    # And delete the ones further down.
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for _get_tc_text
        if 'def _get_tc_text' in line:
            if not seen_tc_text:
                seen_tc_text = True
                new_lines.append(line)
            else:
                # Skip until end of function (simple heuristic: look for next def or async def at indent 0)
                i += 1
                while i < len(lines) and not (lines[i].startswith('def ') or lines[i].startswith('async def ') or lines[i].strip() == '' and i+1 < len(lines) and (lines[i+1].startswith('def ') or lines[i+1].startswith('async def '))):
                    i += 1
                continue
        
        elif 'def _get_refund_text' in line:
            if not seen_refund_text:
                seen_refund_text = True
                new_lines.append(line)
            else:
                i += 1
                while i < len(lines) and not (lines[i].startswith('def ') or lines[i].startswith('async def ')):
                    i += 1
                continue

        elif 'async def _show_tc' in line:
            if not seen_show_tc:
                seen_show_tc = True
                new_lines.append(line)
            else:
                i += 1
                while i < len(lines) and not (lines[i].startswith('def ') or lines[i].startswith('async def ')):
                    i += 1
                continue
        else:
            new_lines.append(line)
        i += 1
    return new_lines

cleaned = clean_duplicates(lines)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(cleaned)

print("Cleaned successfully")
