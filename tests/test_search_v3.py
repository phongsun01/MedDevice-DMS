import asyncio
from db import client as db

async def test():
    await db.connect()
    
    # Test v3 search operator string @@
    # V3 syntax for FULLTEXT is `@@` instead of `@1@`
    query = """
    SELECT 
        id, filename, doc_type, device, content_text[0..100] AS highlight
    FROM document 
    WHERE content_text @@ $query
    """
    
    try:
         print("RUNNING V3 FULLTEXT QUERY...")
         res = await db.query(query, {"query": "CT"})
         print(f"SEARCH RES TYPE: {type(res)}")
         if isinstance(res, list) and len(res) > 0:
             print("RESPONSE WRAP 1:", type(res[0]))
             if isinstance(res[0], list) and len(res[0]) > 0:
                 print("RESPONSE ITEM:", res[0][0])
             else:
                 print("RESPONSE ITEM:", res[0])
         else:
             print("RESPONSE DATA:", res)
    except Exception as e:
         print("QUERY ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test())
