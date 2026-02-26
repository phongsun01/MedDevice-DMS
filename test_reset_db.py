import asyncio
from db import client as db

async def reset_db():
    await db.connect()
    
    # 1. Clear database
    print("Clearing database...")
    await db.query("REMOVE TABLE document; REMOVE TABLE device; REMOVE TABLE device_group; REMOVE TABLE category; REMOVE TABLE audit_log;")
    
    # 2. Apply new schema
    print("Applying new schema...")
    from pathlib import Path
    surql = Path("db/schema.surql").read_text(encoding="utf-8")
    await db.query(surql)
    print("Schema applied.")
    
if __name__ == "__main__":
    asyncio.run(reset_db())
