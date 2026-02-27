import os
import shutil
from pathlib import Path

base_path = Path("D:\\MedicalData")
log_path = base_path.parent / "Antigravity" / "MedDeviceDMS" / "normalize_debug_v2.txt"

# 1. Parse log to get mapping: filename -> intended_path
# Format: MOVE: ...\filename.ext -> cat\group\device\filename.ext
mapping = {}
with open(log_path, "r", encoding="utf-16") as f:
    for line in f:
        line = line.strip()
        if line.startswith("MOVE:") and " -> " in line:
            parts = line.split(" -> ")
            if len(parts) == 2:
                dest_rel_path = parts[1].strip()
                filename = Path(dest_rel_path).name
                mapping[filename] = dest_rel_path

print(f"Loaded {len(mapping)} mappings from log.")

# 2. Scan D:\MedicalData for files that are in the wrong place
moved_count = 0
for root, dirs, files in os.walk(base_path):
    for file in files:
        if file.startswith(".") or file.endswith(".gitkeep"):
            continue
            
        file_path = Path(root) / file
        
        if file in mapping:
            intended_rel = mapping[file]
            intended_abs = base_path / intended_rel
            
            if file_path != intended_abs:
                print(f"Recovering: {file_path.relative_to(base_path)} -> {intended_rel}")
                
                # Create destination directory if not exists
                intended_abs.parent.mkdir(parents=True, exist_ok=True)
                
                # Move
                shutil.move(str(file_path), str(intended_abs))
                moved_count += 1

                # Clean up empty source directory
                try:
                    if not any(file_path.parent.iterdir()):
                        file_path.parent.rmdir()
                except Exception:
                    pass

print(f"Total files recovered: {moved_count}")
