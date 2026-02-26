"""
cleanup_storage.py — Dọn dẹp thư mục storage và reset SurrealDB
- Xoá các thư mục UUID (output của process_upload) trong storage/files
- Giữ lại các thư mục tên thiết bị đúng (human-readable)
- Reset SurrealDB data (giữ nguyên schema)
"""
import asyncio
import re
import shutil
from pathlib import Path

import structlog

log = structlog.get_logger("cleanup")

# UUID-like pattern: 16-30 lowercase alphanumeric chars (SurrealDB record IDs)
_UUID_PATTERN = re.compile(r'^[a-z0-9]{16,30}$')

# Doc-type subfolder names to skip (they are inside device folders, not device folders themselves)
_DOCTYPE_NAMES = {"technical", "config", "price", "contract", "comparison", "link", "other"}

BASE = Path("storage/files")


def _is_uuid(name: str) -> bool:
    return bool(_UUID_PATTERN.match(name))


def scan_and_delete_uuid_folders(dry_run: bool = False) -> dict:
    """Walk storage/files and delete UUID-named device folders."""
    deleted = []
    kept = []

    for cat_dir in sorted(BASE.iterdir()):
        if not cat_dir.is_dir():
            continue

        # Delete entire uncategorized category (all output copies)
        if cat_dir.name == "uncategorized":
            log.info("cleanup.removing_uncategorized", path=str(cat_dir))
            if not dry_run:
                shutil.rmtree(cat_dir)
            deleted.append(f"[CATEGORY] {cat_dir.name}/ (entire)")
            continue

        # For proper categories, look inside group folders for UUID device dirs
        for grp_dir in sorted(cat_dir.iterdir()):
            if not grp_dir.is_dir():
                continue

            has_human_devices = False
            uuid_dirs = []

            for dev_dir in grp_dir.iterdir():
                if not dev_dir.is_dir():
                    continue
                if _is_uuid(dev_dir.name):
                    uuid_dirs.append(dev_dir)
                elif dev_dir.name not in _DOCTYPE_NAMES:
                    has_human_devices = True
                    kept.append(f"{cat_dir.name}/{grp_dir.name}/{dev_dir.name}/")

            # Delete UUID device dirs
            for uuid_dir in uuid_dirs:
                log.info("cleanup.removing_uuid_device", path=str(uuid_dir))
                if not dry_run:
                    shutil.rmtree(uuid_dir)
                deleted.append(f"{cat_dir.name}/{grp_dir.name}/{uuid_dir.name}/")

    return {"deleted": deleted, "kept": kept}


async def reset_surrealdb():
    """Delete all data records while keeping schema."""
    from db import client as db
    await db.connect()
    tables = ["document", "device", "device_group", "category", "audit_log"]
    for table in tables:
        result = await db.query(f"DELETE {table}")
        log.info("db.cleared", table=table)
    log.info("db.reset_complete")


async def main():
    print("\n=== STEP 1: DRY RUN — Scanning UUID folders ===")
    report = scan_and_delete_uuid_folders(dry_run=True)
    print(f"Will DELETE: {len(report['deleted'])} UUID folders")
    print(f"Will KEEP:   {len(report['kept'])} human-named device folders")
    
    print("\nSample DELETE list (first 10):")
    for item in report["deleted"][:10]:
        print(f"  ❌ {item}")
    
    print("\nSample KEEP list (first 10):")
    for item in report["kept"][:10]:
        print(f"  ✅ {item}")

    print("\n=== STEP 2: Executing cleanup ===")
    report2 = scan_and_delete_uuid_folders(dry_run=False)
    print(f"Deleted {len(report2['deleted'])} folders.")

    print("\n=== STEP 3: Resetting SurrealDB ===")
    await reset_surrealdb()
    print("Database cleared. Ready to re-import.")


if __name__ == "__main__":
    asyncio.run(main())
