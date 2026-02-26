import asyncio
from db import client as db

async def test():
    await db.connect()
    
    # Check if Somatom documents exist and have text
    query = """
    SELECT 
        id, filename, device, doc_type, string::len(content_text) AS text_length
    FROM document 
    LIMIT 20
    """
    
    try:
         print("RUNNING DIAGNOSTIC QUERY...")
         res = await db.query(query)
         print(f"DIAGNOSTIC RES TYPE: {type(res)}")
         if isinstance(res, list) and len(res) > 0:
             if isinstance(res[0], list) and len(res[0]) > 0:
                 for item in res[0]:
                     print("ITEM:", item)
             else:
                 for item in res:
                     print("ITEM:", item)
         else:
             print("RESPONSE DATA:", res)
    except Exception as e:
         print("QUERY ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test())
