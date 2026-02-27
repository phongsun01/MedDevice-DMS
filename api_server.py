import os
import json
import logging
from aiohttp import web
from agents.compare_agent import compare_handler

# Cấu hình logging cơ bản
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Antigravity-API")

app = web.Application()

async def handle_chat(request):
    """
    Nhận tin nhắn JSON từ Telegram Bot (Relay) và chuyển cho Agent xử lý.
    """
    try:
        data = await request.json()
        user_id = data.get("user_id")
        query = data.get("query", "")
        
        logger.info(f"Nhận request từ user {user_id}: {query}")
        
        query_lower = query.lower()
        
        # MÔ PHỎNG ANTIGRAVITY AGENT LOGIC BẰNG KEYWORD (Có thể thay bằng LangChain/Gemini SDK)
        # Trong tương lai API này cần truyền thẳng query vào Gemini Function Calling
        
        if "so sánh" in query_lower or "compare" in query_lower:
            # Simple keyword extraction for MVP
            if "examion" in query_lower and ("fuji" in query_lower or "68s" in query_lower):
                device_a = "Examion"
                device_b = "Fuji"
            else:
                # Fallback to general comparison if cannot parse cleanly
                device_a = ""
                device_b = ""
                
            if device_a and device_b:
                logger.info(f"Agent quyết định gọi compare_handler cho: {device_a} vs {device_b}")
                md_text, xlsx_path = await compare_handler(device_a, device_b, user_id)
                response_payload = {
                    "text": f"Dưới đây là kết quả phân tích theo yêu cầu của bạn (Tôi đã dùng `compare_agent.py` ngầm):\n\n<pre>{md_text}</pre>",
                    "file_path": xlsx_path
                }
            else:
                response_payload = {
                    "text": "Tôi hiểu bạn muốn so sánh. Xin vui lòng cung cấp hai tên thiết bị rõ ràng hơn. (Ví dụ: So sánh Examion và Fuji)",
                    "file_path": None
                }

        elif "danh sách" in query_lower or "liệt kê" in query_lower:
             response_payload = {
                "text": "Tính năng hỏi/đáp tự do về danh sách thư mục đang được Antigravity phân tích, vui lòng chờ...",
                "file_path": None
            }
        else:
            response_payload = {
                "text": "💡 <b>Antigravity Agent Mode:</b>\n\nTôi vừa nhận được tin nhắn của bạn. Hiện tại hệ thống đang được cấu hình để nhận biết ý định. Bạn có thử hỏi 'so sánh ...' không?",
                "file_path": None
            }
            
        return web.json_response(response_payload)
        
    except Exception as e:
        logger.error(f"Lỗi API: {e}")
        return web.json_response({"text": f"Lỗi nội bộ API: {e}", "file_path": None}, status=500)


app.router.add_post('/api/chat', handle_chat)

if __name__ == '__main__':
    logger.info("Khởi động Antigravity Headless API Server trên cổng 8081...")
    web.run_app(app, host='127.0.0.1', port=8081)
