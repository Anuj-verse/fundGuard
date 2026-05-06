import json
import os

log_file = "/home/anuj-gope/.gemini/antigravity/brain/ae983c73-104c-40e1-b741-4859c41321cf/.system_generated/logs/overview.txt"
files = {}

with open(log_file, "r") as f:
    for line in f:
        if not line.strip().startswith("{"): continue
        try:
            data = json.loads(line)
        except:
            continue
        if "tool_calls" in data:
            for call in data["tool_calls"]:
                if call["name"] == "write_to_file":
                    target = call["args"].get("TargetFile", "").strip('"')
                    content = call["args"].get("CodeContent", "")
                    files[target] = content
                elif call["name"] in ("replace_file_content", "multi_replace_file_content"):
                    target = call["args"].get("TargetFile", "").strip('"')
                    # We skip replace, we just want the base files that we destroyed.

# Also we need to apply the replace to the files that were modified by replace_file_content during the conversation
import re
for target, content in files.items():
    if "synthetic_generator" in target:
        # If it's a locale file, change target path
        if "/locale/" in target:
            target = target.replace("/locale/", "/localization/")
        
        # Replace the imports
        content = content.replace("synthetic_generator.locale", "synthetic_generator.localization")
        
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as f:
                f.write(content)
            print("Recovered:", target)
        except Exception as e:
            print("Failed", target, e)
