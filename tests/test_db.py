import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname('__file__'), '..')))
from db.client import connect, query, apply_schema

async def main():
    await connect()
    print("Dropping tables...")
    await query("REMOVE TABLE category;")
    await query("REMOVE TABLE device_group;")
    await query("REMOVE TABLE device;")
    await query("REMOVE TABLE document;")
    print("Applying schema...")
    await apply_schema()
    print("Schema applied!")
    
asyncio.run(main())
