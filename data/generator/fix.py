import glob
import re
import os

for filepath in glob.glob('/home/anuj-gope/fundguard/fundguard/data/generator/src/synthetic_generator/fraud/*.py'):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix the corrupted backslashes
    content = content.replace(r"{\'\'.join(random.choices(\'0123456789ABCDEF\', k=12))}", "{''.join(random.choices('0123456789ABCDEF', k=12))}")
    content = content.replace(r"{\'\'.join(random.choices(\'0123456789ABCDEF\', k=16))}", "{''.join(random.choices('0123456789ABCDEF', k=16))}")
    
    # Add import random if missing
    if 'import random' not in content and 'random.choices' in content:
        content = content.replace('import uuid', 'import random\nimport uuid')
        
    with open(filepath, 'w') as f:
        f.write(content)
