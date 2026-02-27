import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import settings
from db.client import connect, query

async def main():
    try:
        print(f"Connecting to {settings.SURREAL_URL} NS={settings.SURREAL_NS} DB={settings.SURREAL_DB}")
        client = await connect()
        res = await query('SELECT * FROM document LIMIT 2000')
        print(f"Query returned {len(res)} results.")
        if res:
            docs = res[0]
            if isinstance(docs, dict):
                docs = docs.get("result", [])
            print(f"Docs type: {type(docs)}, length: {len(docs)}")
            if len(docs) > 0:
                print(f"First doc: {docs[0]}")
    except Exception as e:
        print(f"ERROR: {e}")

asyncio.run(main())
