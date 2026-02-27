"""
MedDevice DMS - Antigravity First / Webhook Relay Handler
"""
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import aiohttp
import os
import time

router = Router()

# This is the port where api_server.py will listen
ANTIGRAVITY_API_URL = "http://localhost:8081/api/chat"


@router.message(Command("ask"))
@router.message(F.text & ~F.text.startswith("/"))
async def relay_to_antigravity(message: Message):
    """
    Forward free-text messages to Antigravity Headless API.
    """
    # 1. Answer user so they know we are processing it
    wait_msg = await message.answer("⏳ *Antigravity Agent* đang suy luận và phân tích thư mục storage/files...", parse_mode="Markdown")
    
    # Extract query text if it's a command /ask or just free text
    text = message.text
    if text.startswith("/ask"):
        text = text[4:].strip()
        
    if not text:
        await wait_msg.edit_text("Vui lòng hỏi tôi một câu hỏi cụ thể, ví dụ: 'So sánh máy Examion và Fuji'")
        return

    # 2. Build payload
    payload = {
        "user_id": message.from_user.id,
        "query": text,
        "chat_id": message.chat.id
    }
    
    try:
        # 3. Request API Server
        async with aiohttp.ClientSession() as session:
            async with session.post(ANTIGRAVITY_API_URL, json=payload, timeout=120) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    
                    # 4. Return results
                    reply_text = result.get('text', "Tôi đã xử lý xong nhưng không có văn bản trả về.")
                    await wait_msg.edit_text(reply_text, parse_mode="HTML")
                    
                    if 'file_path' in result and result['file_path']:
                        file_path = result['file_path']
                        if os.path.exists(file_path):
                            await message.answer_document(FSInputFile(file_path))
                        else:
                            await message.answer(f"⚠️ Agent báo lỗi: Không tìm thấy file `{file_path}` để gửi.")
                else:
                    await wait_msg.edit_text(f"⚠️ Lỗi kết nối Antigravity API: {resp.status}\nBạn đã chạy `api_server.py` chưa?")
    except Exception as e:
        await wait_msg.edit_text(f"⚠️ Lỗi xử lý Relay: {e}\nBạn đã chạy `api_server.py` ở cổng 8081 chưa?")
