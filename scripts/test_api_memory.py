import asyncio
import aiohttp
import json
import sys

# Ensure UTF-8 output for Windows console
sys.stdout.reconfigure(encoding='utf-8')

async def test_api_memory():
    url = "http://127.0.0.1:8081/api/chat"
    user_id = 9999 # Test User ID
    
    async with aiohttp.ClientSession() as session:
        # Lượt 1: Hỏi thông thường (LLM trả lời text thường)
        print("\n--- LUOT 1: Hoi thong thuong ---")
        q1 = "Xin chao, toi la bac si o benh vien."
        print(f"User: {q1}")
        async with session.post(url, json={"user_id": user_id, "query": q1}) as resp:
            data = await resp.json()
            print(f"Bot: {data.get('text')}")

        # Lượt 2: Hỏi máy móc (ngôn ngữ tự nhiên, không nhắc đến so sánh)
        print("\n--- LUOT 2: Hoi may moc (Thiet lap Context) ---")
        q2 = "Hom nay toi muon tim hieu thong tin ve 2 dong may: Examion va Fuji."
        print(f"User: {q2}")
        async with session.post(url, json={"user_id": user_id, "query": q2}) as resp:
            data = await resp.json()
            print(f"Bot: {data.get('text')}")

        # Lượt 3: Gọi lệnh so sánh DỰA TRÊN NGỮ CẢNH cũ (không lặp lại tên máy đầy đủ)
        # LLM bắt được function call và gọi compare_agent
        print("\n--- LUOT 3: Kich hoat Intent (So sanh Dua tren Context) ---")
        q3 = "Ban so sanh giup toi hai dong may do xem khac biet ra sao nhe."
        print(f"User: {q3}")
        async with session.post(url, json={"user_id": user_id, "query": q3}, timeout=120) as resp:
            data = await resp.json()
            print(f"Bot (Text): {data.get('text')[:200]}...") # In một phần kết quả
            print(f"Bot (File Path): {data.get('file_path')}")

if __name__ == "__main__":
    print("Testing Memory Manager & Intent Routing (Make sure api_server.py is running)")
    asyncio.run(test_api_memory())

