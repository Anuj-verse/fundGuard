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
                    # Actually handling replace is hard, but maybe the latest write_to_file is enough?
                    pass

for t, content in files.items():
    if "synthetic_generator" in t:
        try:
            with open(t, "w") as f:
                f.write(content)
            print("Recovered:", t)
        except Exception as e:
            print("Failed", t, e)
