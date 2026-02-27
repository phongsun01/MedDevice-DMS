import os
import re
import shutil
import json
import argparse
import sys
from pathlib import Path
from unidecode import unidecode

# Ensure stdout can handle Vietnamese characters in logs
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for older python versions
        pass

def to_kebab(text):
    if not text: return "unknown"
    text = unidecode(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text if text else "unknown"

class Normalizer:
    def __init__(self, base_path, config_path, dry_run=True):
        self.base_path = Path(base_path)
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.dry_run = dry_run
        self.prefixes = self.config.get("prefixes", {})
        self.suffixes = self.config.get("suffixes", {})
        self.keywords = self.config.get("keywords", {})
        
        # Hardcoded mapping for known items based on PRD
        self.device_to_group = {
            "somatom-go-now": "ct-scan",
            "ct-128-somatom-go-top": "ct-scan",
            "he-thong-ct-dem-photon": "ct-scan",
            "arietta-50": "sieu-am",
            "acuson-juniper": "sieu-am",
            "acuson-maple": "sieu-am",
            "acuson-redwood": "sieu-am",
            "acuson-sequoia-select": "sieu-am",
            "arietta-750v": "sieu-am",
            "resona-i9-exp": "sieu-am",
            "cios-fit": "c-arm",
            "cios-select": "c-arm",
            "azurion-7b20": "dsa",
            "siemens-dsa": "dsa",
            "siemens-0-55": "mri",
            "examion": "x-quang",
            "fdr-68s": "x-quang",
            "lida-800": "may-sinh-hoa",
            "lida-500": "may-sinh-hoa"
        }

        self.known_groups = [
            "ct-scan", "sieu-am", "c-arm", "dsa", "mri", "x-quang",
            "may-sinh-hoa", "may-huyet-hoc", "may-mien-dich", "xet-nghiem-sinh-hoa",
            "he-thong-x-quang", "he-thong-ct", "may-chup-cat-lop"
        ]

    def classify_file(self, filename):
        name = unidecode(filename).lower()
        doc_type = "other"
        language = None
        sub_types = []

        # Check prefixes keyword
        for key, words in self.keywords.items():
            if any(word in name for word in words):
                if key in self.prefixes:
                    doc_type = key
                elif key in ['vi', 'en']:
                    language = key
                else:
                    sub_types.append(key)

        return doc_type, language, sub_types

    def get_new_filename(self, filename):
        doc_type, language, sub_types = self.classify_file(filename)
        prefix = self.prefixes.get(doc_type, "other-")
        
        # Suffixes
        suffix_str = ""
        # Deduplicate sub_types (e.g. bidding and compliance might both be config keywords)
        sub_types = sorted(list(set(sub_types)))
        if sub_types:
            for st in sub_types:
                suffix_str += self.suffixes.get(st, f"-{st}")
        if language:
            suffix_str += self.suffixes.get(language, f"-{language}")
            
        stem = to_kebab(Path(filename).stem)
        # Remove existing prefixes/suffixes from stem if they are already there to avoid tech-tech-
        for p in self.prefixes.values():
            if stem.startswith(p): stem = stem[len(p):].strip("-")
        for s in self.suffixes.values():
            if stem.endswith(s): stem = stem[:-len(s)].strip("-")
            
        new_name = f"{prefix}{stem}{suffix_str}{Path(filename).suffix}"
        return new_name

    def normalize(self):
        print(f"{'[DRY RUN] ' if self.dry_run else ''}Normalizing {self.base_path}")
        
        # Step 1: Collect all files
        all_files = []
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.startswith(".") or file.endswith(".gitkeep"): continue
                all_files.append(Path(root) / file)

        # Step 2: Plan movements
        plan = []
        for file_path in all_files:
            rel = file_path.relative_to(self.base_path)
            parts = rel.parts
            
            if len(parts) < 2:
                print(f"Skipping file at root: {file_path}")
                continue
                
            cat = to_kebab(parts[0])
            group = "chung"
            device = "unknown"
            is_archive = "archive" in [p.lower() for p in parts]
            
            # Logic to infer Group and Device (v2.1)
            p1 = to_kebab(parts[1])
            
            # Step 1: Detect Device and Group
            current_device = "unknown"
            current_group = "other-group"
            
            if p1 == "chung" and len(parts) >= 3:
                # If we are in the 'chung' folder I accidentally created, look deeper
                current_device = to_kebab(parts[2])
            elif p1 in self.known_groups:
                current_group = p1
                if len(parts) >= 3:
                    current_device = to_kebab(parts[2])
                else:
                    current_device = "chung"
            else:
                current_device = p1

            # Step 2: Refine Group based on Device Name Prefix
            if current_group == "other-group":
                # Check mapping first
                if current_device in self.device_to_group:
                    current_group = self.device_to_group[current_device]
                else:
                    # Check prefixes (e.g. sieu-am-acuson -> sieu-am)
                    for kg in sorted(self.known_groups, key=len, reverse=True):
                        if current_device.startswith(kg + "-"):
                            current_group = kg
                            break
            
            group = current_group
            device = current_device
            
            # DEBUG
            # print(f"DEBUG: {rel} -> cat={cat}, group={group}, device={device}")

            # Flatten all files into Device root, unless it's in an archive folder
            new_filename = self.get_new_filename(file_path.name)
            
            if is_archive:
                target_dir = self.base_path / cat / group / device / "archive"
            else:
                target_dir = self.base_path / cat / group / device
                
            target_path = target_dir / new_filename
            plan.append((file_path, target_path))

        # Step 3: Execute
        executed = 0
        for src, dst in plan:
            if src == dst: continue
            
            print(f"MOVE: {src.relative_to(self.base_path)} -> {dst.relative_to(self.base_path)}")
            if not self.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                # Handle conflict
                if dst.exists():
                    dst = dst.with_name(f"{dst.stem}_dup_{executed}{dst.suffix}")
                shutil.move(str(src), str(dst))
            executed += 1

        # Step 4: Cleanup empty folders (except base_path)
        if not self.dry_run:
            self.cleanup_empty_folders(self.base_path)

        print(f"\nTotal files planned/moved: {executed}")

    def cleanup_empty_folders(self, path):
        for root, dirs, files in os.walk(path, topdown=False):
            for d in dirs:
                dir_path = Path(root) / d
                if not any(dir_path.iterdir()):
                    print(f"Removing empty folder: {dir_path}")
                    dir_path.rmdir()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="D:\\MedicalData")
    parser.add_argument("--config", default="config\\data_naming.json")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    
    norm = Normalizer(args.path, args.config, dry_run=not args.run)
    norm.normalize()
