import os, glob

for f in glob.glob("plugins/*.py"):
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    
    new_content = content.replace(
        '"<i>Process Cancelled Successfully!</i>")', 
        '"<i>Process Cancelled Successfully!</i>", reply_markup=ReplyKeyboardRemove())'
    )
    
    if new_content != content:
        with open(f, "w", encoding="utf-8") as file:
            file.write(new_content)
        print(f"Fixed missing ReplyKeyboardRemove in {f}")
