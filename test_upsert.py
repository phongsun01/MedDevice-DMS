import asyncio
from db import client as db

async def test():
    await db.connect()
    try:
        res = await db.query(
            "UPSERT type::record($id) CONTENT { name: $name }",
            {"id": "category:test", "name": "test"}
        )
        print("UPSERT OK:", res)
    except Exception as e:
        print("UPSERT ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test())
