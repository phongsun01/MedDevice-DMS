"""
MedDevice DMS — Normalize folder names to kebab-case.
Usage:
    python scripts/normalize_folders.py --dry-run   # Preview only
    python scripts/normalize_folders.py             # Execute renaming
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

try:
    from unidecode import unidecode
except ImportError:
    print("Missing dependency: pip install unidecode")
    sys.exit(1)


def to_kebab(text: str) -> str:
    """Convert any Vietnamese folder name to kebab-case."""
    text = unidecode(text)             # Remove diacritics
    text = text.lower()
    text = text.replace("_", "-")     # snake_case → kebab
    # Replace multiple spaces/hyphens/special chars with single hyphen
    import re
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


def plan_normalize(base_path: Path) -> list[dict]:
    """Scan one level of base_path and build rename/merge plan."""
    actions = []
    seen: dict[str, Path] = {}  # kebab_name → first_path

    for entry in sorted(base_path.iterdir()):
        if not entry.is_dir():
            continue
        target_name = to_kebab(entry.name)
        target_path = base_path / target_name

        if entry.name == target_name:
            # Already correct
            seen[target_name] = entry
            continue

        if target_name in seen:
            # Merge into existing folder
            actions.append({
                "action": "merge",
                "src": entry,
                "dst": seen[target_name],
            })
        else:
            seen[target_name] = target_path
            actions.append({
                "action": "rename",
                "src": entry,
                "dst": target_path,
            })

    return actions


def execute_actions(actions: list[dict], dry_run: bool) -> None:
    merged = renamed = skipped = 0
    for act in actions:
        src: Path = act["src"]
        dst: Path = act["dst"]
        tag = "[DRY-RUN] " if dry_run else ""

        if act["action"] == "rename":
            print(f"{tag}RENAME: {src.name!r} → {dst.name!r}")
            if not dry_run:
                src.rename(dst)
            renamed += 1

        elif act["action"] == "merge":
            print(f"{tag}MERGE:  {src.name!r} → {dst.name!r} (merge {src})")
            if not dry_run:
                # Move contents of src into dst, then remove src
                for item in src.iterdir():
                    dest_item = dst / item.name
                    if dest_item.exists():
                        print(f"  ⚠️  CONFLICT: {item.name} already in dst, skipping")
                        skipped += 1
                    else:
                        shutil.move(str(item), str(dest_item))
                src.rmdir()
            merged += 1

    print()
    print("─" * 50)
    if dry_run:
        print(f"[DRY-RUN] Would: rename={renamed}, merge={merged}, conflicts={skipped}")
        print("Run without --dry-run to apply changes.")
    else:
        print(f"Done: renamed={renamed}, merged={merged}, conflicts(skipped)={skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize storage/files folder names to kebab-case.")
    parser.add_argument("--path", default="storage/files", help="Base path to normalize (default: storage/files)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not rename")
    parser.add_argument("--recursive", action="store_true", help="Also normalize sub-level folders (group, device)")
    args = parser.parse_args()

    base = Path(args.path)
    if not base.exists():
        print(f"Error: path '{base}' not found.")
        sys.exit(1)

    print(f"Normalizing: {base.resolve()}")
    print()

    if args.recursive:
        # Process bottom-up to avoid path invalidation
        import os
        for root, dirs, files in os.walk(base, topdown=False):
            root_path = Path(root)
            actions = plan_normalize(root_path)
            if actions:
                execute_actions(actions, args.dry_run)
    else:
        actions = plan_normalize(base)
        if actions:
            execute_actions(actions, args.dry_run)


if __name__ == "__main__":
    main()
