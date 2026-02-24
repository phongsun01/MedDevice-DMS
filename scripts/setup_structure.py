"""
MedDevice DMS — Phase 0.2 + 0.3
- Create Group folders under thiet-bi-chan-doan-hinh-anh
- Move Device folders into correct Group
- Create doc_type subfolders inside each Device folder
Usage:
    python scripts/setup_structure.py --dry-run
    python scripts/setup_structure.py
"""
import argparse
import shutil
from pathlib import Path
import re
from unidecode import unidecode

# ─── Phân nhóm device theo PRD Section 2.3 ───────────────────────────────────
DEVICE_TO_GROUP = {
    "somatom-go-now":           "ct-scan",
    "ct-128-somatom-go-top":    "ct-scan",
    "he-thong-ct-dem-photon":   "ct-scan",
    "arietta-50":               "sieu-am",
    "sieu-am-acuson-juniper":   "sieu-am",
    "sieu-am-acuson-maple":     "sieu-am",
    "sieu-am-acuson-redwood":   "sieu-am",
    "sieu-am-acuson-sequoia-select": "sieu-am",
    "sieu-am-arietta-750v":     "sieu-am",
    "sieu-am-resona-i9-exp":    "sieu-am",
    "c-arm-siemens-cios-fit":   "c-arm",
    "c-arm-siemens-cios-select":"c-arm",
    "dsa-azurion-7b20":         "dsa",
    "dsa-siemens":              "dsa",
    "mri-siemens-0-55":         "mri",
    "x-quang-examion":          "x-quang",
    "x-quang-fdr-68s":          "x-quang",
}

DOC_SUBFOLDERS = [
    "technical/vi", "technical/en",
    "config/bidding", "config/compliance", "config/quotation", "config/advertising", "config/basic",
    "price", "contract", "comparison", "other/archive",
]

CHAN_DOAN_PATH = Path("storage/files/thiet-bi-chan-doan-hinh-anh")

def normalize_name(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", unidecode(text).lower()).strip("-")
    return slug

def setup_groups(dry_run: bool) -> None:
    tag = "[DRY-RUN] " if dry_run else ""
    moved = skipped = created = 0

    current_devices = {d.name: d for d in CHAN_DOAN_PATH.iterdir() if d.is_dir() and d.name not in set(DEVICE_TO_GROUP.values())}

    for device_name, group_name in DEVICE_TO_GROUP.items():
        group_path = CHAN_DOAN_PATH / group_name
        if not group_path.exists():
            print(f"{tag}CREATE group: {group_name}/")
            if not dry_run:
                group_path.mkdir(parents=True, exist_ok=True)
            created += 1

        device_src = None
        for name, path in current_devices.items():
            if name == device_name or normalize_name(name) == device_name:
                device_src = path
                break

        if device_src is None:
            # Maybe already moved
            if (group_path / device_name).exists():
                 print(f"  ✅ Already in group: {group_name}/{device_name}")
                 skipped += 1
            else:
                 print(f"  ⚠️  Not found: {device_name}")
                 skipped += 1
            continue

        device_dst = group_path / device_name
        if device_src.absolute() == device_dst.absolute():
             continue
        if device_dst.exists():
            print(f"  ⚠️  Destination exists: {group_name}/{device_name}")
            skipped += 1
            continue

        print(f"{tag}MOVE: {device_src.name} → {group_name}/{device_name}")
        if not dry_run:
            shutil.move(str(device_src), str(device_dst))
        moved += 1

    print(f"\n[Phase 0.2] Groups created: {created}, Devices moved: {moved}, Skipped: {skipped}\n")


def create_subfolders(dry_run: bool) -> None:
    tag = "[DRY-RUN] " if dry_run else ""
    created = 0
    base = Path("storage/files")

    # Only process inside proper device folders (those that are direct children of Groups)
    # We'll specifically target the groups we know about in thiet-bi-chan-doan-hinh-anh for now
    # to avoid ruining other random folders
    
    if not CHAN_DOAN_PATH.exists(): return
    
    for group_folder in CHAN_DOAN_PATH.iterdir():
        if not group_folder.is_dir() or group_folder.name not in set(DEVICE_TO_GROUP.values()):
            continue
            
        for device_folder in group_folder.iterdir():
            if not device_folder.is_dir(): continue
            
            # Check if this is a weird hash folder (like i9u6tljf1gic20z6cz2w)
            if re.match(r'^[a-z0-9]{20}$', device_folder.name):
                continue
                
            for sub in DOC_SUBFOLDERS:
                sub_path = device_folder / sub
                if not sub_path.exists():
                    print(f"{tag}MKDIR: {sub_path.relative_to(base)}")
                    if not dry_run:
                        sub_path.mkdir(parents=True, exist_ok=True)
                    created += 1

    print(f"\n[Phase 0.3] Subfolders created: {created}\n")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not CHAN_DOAN_PATH.exists():
        print(f"Error: {CHAN_DOAN_PATH} not found. Run normalize_folders.py first.")
        return

    setup_groups(args.dry_run)
    create_subfolders(args.dry_run)

if __name__ == "__main__":
    main()
