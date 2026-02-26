import asyncio
import os
import re
from pathlib import Path
import structlog

from config import settings
from db import client as db
from agents.parse_agent import process_upload

log = structlog.get_logger("import_local")

# UUID-like pattern (from previous bug that created random folder names)
_UUID_PATTERN = re.compile(r'^[a-z0-9]{16,}$')

def _is_uuid_like(name: str) -> bool:
    """Return True if the folder name looks like a random ID (corrupted data)."""
    return bool(_UUID_PATTERN.match(name))


async def sync_structure():
    """Scan storage/files and sync with SurrealDB."""
    base_path = Path("storage/files")
    if not base_path.exists():
        log.error("storage.missing", path=str(base_path))
        return

    # Categories are the top-level folders
    for cat_dir in sorted(base_path.iterdir()):
        if not cat_dir.is_dir(): continue
        if _is_uuid_like(cat_dir.name):
            log.warning("sync.skip_uuid_folder", name=cat_dir.name, level="category")
            continue
        
        cat_name = cat_dir.name
        log.info("sync.category", name=cat_name)
        
        # 1. Create/Get Category
        cat_results = await db.query(
            "SELECT id FROM category WHERE name = $name", {"name": cat_name}
        )
        if cat_results:
            # Handle both [[{...}]] and [{...}]
            first_res = cat_results[0]
            if isinstance(first_res, list) and first_res:
                cat_id = first_res[0]["id"]
            elif isinstance(first_res, dict):
                cat_id = first_res["id"]
            else:
                cat_rec = await db.create("category", {"name": cat_name, "display_name": cat_name})
                cat_id = cat_rec["id"]
        else:
            cat_rec = await db.create("category", {"name": cat_name, "display_name": cat_name})
            cat_id = cat_rec["id"]

        # Level 2 could be Groups or Devices directly
        for sub_dir in sorted(cat_dir.iterdir()):
            if not sub_dir.is_dir(): continue
            if _is_uuid_like(sub_dir.name):
                log.warning("sync.skip_uuid_folder", name=sub_dir.name, level="group/device")
                continue
            
            # Check if this sub_dir contains folders (it's a group) or files (it's a device)
            has_subfolders = any(d.is_dir() for d in sub_dir.iterdir())
            
            if has_subfolders:
                # 2a. Level 2 is a Group
                group_name = sub_dir.name
                log.info("sync.group", name=group_name, cat=cat_name)
                
                group_results = await db.query(
                    "SELECT id FROM device_group WHERE name = $name AND category = $cat",
                    {"name": group_name, "cat": cat_id}
                )
                if group_results:
                    first_res = group_results[0]
                    if isinstance(first_res, list) and first_res:
                        group_id = first_res[0]["id"]
                    elif isinstance(first_res, dict):
                        group_id = first_res["id"]
                    else:
                        group_rec = await db.create("device_group", {
                            "name": group_name, "category": cat_id, "display_name": group_name
                        })
                        group_id = group_rec["id"]
                else:
                    group_rec = await db.create("device_group", {
                        "name": group_name, "category": cat_id, "display_name": group_name
                    })
                    group_id = group_rec["id"]
                
                # Level 3 are Devices
                for device_dir in sub_dir.iterdir():
                    if not device_dir.is_dir(): continue
                    await process_device_dir(device_dir, group_id)
            else:
                # 2b. Level 2 is a Device (Group = "Chung")
                group_name = "Chung"
                group_results = await db.query(
                    "SELECT id FROM device_group WHERE name = $name AND category = $cat",
                    {"name": group_name, "cat": cat_id}
                )
                if group_results:
                    first_res = group_results[0]
                    if isinstance(first_res, list) and first_res:
                        group_id = first_res[0]["id"]
                    elif isinstance(first_res, dict):
                        group_id = first_res["id"]
                    else:
                        group_rec = await db.create("device_group", {
                            "name": group_name, "category": cat_id, "display_name": "Nhóm chung"
                        })
                        group_id = group_rec["id"]
                else:
                    group_rec = await db.create("device_group", {
                        "name": group_name, "category": cat_id, "display_name": "Nhóm chung"
                    })
                    group_id = group_rec["id"]
                
                await process_device_dir(sub_dir, group_id)

async def process_device_dir(device_dir: Path, group_id: str):
    """Import files from a device directory."""
    device_name = device_dir.name
    log.info("sync.device", name=device_name)
    
    # 3. Create/Get Device
    dev_results = await db.query(
        "SELECT id FROM device WHERE name = $name AND device_group = $group",
        {"name": device_name, "group": group_id}
    )
    if dev_results:
        first_res = dev_results[0]
        if isinstance(first_res, list) and first_res:
            device_id = first_res[0]["id"]
        elif isinstance(first_res, dict):
            device_id = first_res["id"]
        else:
            dev_rec = await db.create("device", {
                "name": device_name, "device_group": group_id, "description": device_name, "specs": {}
            })
            device_id = dev_rec["id"]
    else:
        dev_rec = await db.create("device", {
            "name": device_name, 
            "model": "Chưa xác định", 
            "brand": "Chưa xác định",
            "device_group": group_id, 
            "notes": device_name
        })
        device_id = dev_rec["id"]

    # Recursively find all files in device_dir
    for root, _, files in os.walk(str(device_dir)):
        for filename in files:
            if filename.startswith(".") or filename.endswith(".gitkeep"): continue
            
            file_path = Path(root) / filename
            # Use process_upload to handle extraction, storage move, and wiki update
            # We copy instead of move if we want to keep storage/files as source
            # But process_upload does 'shutil.move'. 
            # To keep user's original structure, let's copy to a temp and process.
            import tempfile
            import shutil
            
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_file = Path(tmp_dir) / filename
                shutil.copy(str(file_path), str(tmp_file))
                
                try:
                    # Let process_upload take care of categorization by filename if possible
                    # We can also pass a hint via caption if we want
                    await process_upload(str(tmp_file), device_id, caption=None, telegram_user_id="SYSTEM")
                    log.info("import.file.success", file=filename, device=device_name)
                except Exception as e:
                    log.error("import.file.failed", file=filename, error=str(e))

async def main():
    await db.connect()
    await sync_structure()
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
