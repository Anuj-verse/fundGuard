import json
import os
import re

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
                    target = call["args"].get("TargetFile", "")
                    if target.startswith('"'):
                        target = json.loads(target)
                    content = call["args"].get("CodeContent", "")
                    if content.startswith('"'):
                        try:
                            content = json.loads(content)
                        except:
                            pass
                    files[target] = content

for target, content in files.items():
    if "synthetic_generator" in target:
        if "/locale/" in target:
            target = target.replace("/locale/", "/localization/")
        
        content = content.replace("synthetic_generator.locale", "synthetic_generator.localization")
        
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as f:
                f.write(content)
            print("Recovered (decoded):", target)
        except Exception as e:
            print("Failed", target, e)
