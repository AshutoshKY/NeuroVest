"""
Quick fix for streamlit_app.py indentation
"""
import re

# Read the file
with open('streamlit_app.py', 'r') as f:
    lines = f.readlines()

# Find and fix the problematic section (around line 194-310)
fixed_lines = []
in_problem_section = False

for i, line in enumerate(lines, 1):
    # Lines 194-310 need to be reduced by 4 spaces (one tab level)
    if 194 <= i <= 310:
        if line.startswith('                            '):  # 28 spaces (7 tabs)
            # Reduce to 24 spaces (6 tabs)
            fixed_line = line[4:]
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

# Write back
with open('streamlit_app.py', 'w') as f:
    f.writelines(fixed_lines)

print("✅ Fixed indentation in streamlit_app.py")
