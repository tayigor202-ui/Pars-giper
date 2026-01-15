
import os

file_path = "check_violations.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
indent_mode = False

for line in lines:
    # Trigger start of indentation (After the loop def)
    if "for attempt in range(2):" in line:
        new_lines.append(line)
        indent_mode = True
        continue
        
    # Trigger end of indentation (Before logic that shouldn't be indented, if any)
    # Actually we want to indent ALMOST everything until the except block ends.
    # The except block ends at line 447.
    # The next section is "# --- PROXY FORWARDER"
    
    if "# --- PROXY FORWARDER" in line:
        indent_mode = False
        
    if indent_mode:
        # Check if line is already indented (we just added the loop)
        # We need to indent everything that was previously at level 1 (inside try) to level 2 (inside loop)
        # or logic that was at level 1.
        # Current logic starts at indentation 8 spaces (inside try -> function? no its inside loop now)
        
        # The code structure:
        # try:
        #    ...
        #    for attempt in range(2):
        #        ...
        #        <BLOCK TO INDENT>
        #    ...
        # except:
        
        # The block was previously:
        #        # --- EXTRACT...
        #        real_seller = ...
        
        # We want to add 4 spaces to it.
        if line.strip() != "":
            new_lines.append("    " + line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Indentation fixed.")
