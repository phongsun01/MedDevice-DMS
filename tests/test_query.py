import asyncio
from db import client as db

async def test():
    await db.connect()
    # Thử gọi db.query
    query = "SELECT * FROM category LIMIT 1"
    res = await db.query(query)
    print("CATEGORY RES TYPE:", type(res))
    print("CATEGORY RES:", res)
    
    from agents.search_agent import search_documents
    print("--- SEARCH ---")
    res = await search_documents("CT")
    print("SEARCH RES TYPE:", type(res))
    if len(res) > 0:
        print("FIRST ITEM TYPE:", type(res[0]))
        print("FIRST ITEM:", res[0])
        
if __name__ == "__main__":
    asyncio.run(test())
