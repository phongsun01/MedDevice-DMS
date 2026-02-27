import os
import json
import logging
from aiohttp import web
from agents.compare_agent import compare_handler
from core.memory import memory
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from config import settings

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Antigravity-API")

app = web.Application()

# Khởi tạo Gemini Client
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Define System Prompt
SYSTEM_PROMPT = """Bạn là Antigravity Agent - hệ thống AI nội bộ quản lý tài liệu y tế (MedDevice DMS).
Nhiệm vụ của bạn là đọc tin nhắn của người dùng và lịch sử chat (nếu có), hiểu ngữ cảnh và trả lời.
Bạn có khả năng gọi hàm (function_calling) để thực hiện các nghiệp vụ đặc biệt nếu cần.
Nếu người dùng yêu cầu "so sánh thiết bị", bạn PHẢI gọi công cụ 'compare_devices_tool'.
Nếu chỉ hỏi đáp thông thường, bạn trả lời bằng tiếng Việt chuyên nghiệp, ngắn gọn.
"""

def get_gemini_response_with_tools(query: str, history_msgs: list) -> tuple[str, str | None]:
    """
    Gọi Gemini API, truyền kèm ngữ cảnh hội thoại và bộ Tools (ví dụ: compare_devices_tool).
    """
    # 1. Khai báo schema cho function calling
    compare_device_declaration = {
        "name": "compare_devices_tool",
        "description": "Gọi hàm này khi người dùng muốn so sánh thông số kỹ thuật giữa 2 thiết bị. Yêu cầu truyền đúng tên thiết bị vào.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "device_a": {
                    "type": "STRING",
                    "description": "Tên dòng máy thứ nhất (ngắn gọn, ví dụ: 'Examion', 'Fuji 68s')",
                },
                "device_b": {
                    "type": "STRING",
                    "description": "Tên dòng máy thứ hai (ngắn gọn, ví dụ: 'Somatom Go Now')",
                }
            },
            "required": ["device_a", "device_b"]
        }
    }

    # 2. Chuẩn bị lịch sử
    contents = []
    for msg in history_msgs:
        # Gemini nhận role "user" hoặc "model"
        # contents.append({"role": msg["role"], "parts": [{"text": msg["content"]}]}) # Cách cũ
        contents.append(
            types.Content(
                role=msg["role"],
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )
        
    # Thêm câu hiện tại
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )
    )

    # 3. Request Gemini
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.0,
                tools=[types.Tool(function_declarations=[compare_device_declaration])]
            ),
        )

        # 4. Xử lý phản hồi (Function Call hay Text trả lời thường?)
        if response.function_calls:
            for fn_call in response.function_calls:
                if fn_call.name == "compare_devices_tool":
                    args = fn_call.args
                    dev_a = args.get("device_a")
                    dev_b = args.get("device_b")
                    logger.info(f"Gemini Intent Routing: Trigger compare_devices_tool cho {dev_a} vs {dev_b}")
                    # Trả về tín hiệu để main_handler phía ngoài gọi async function
                    return "INTENT_COMPARE", json.dumps({"device_a": dev_a, "device_b": dev_b})

        # Xử lý text thông thường
        if response.text:
            return response.text, None
            
        return "Xin lỗi, tôi không thể xử lý yêu cầu lúc này.", None
    except Exception as e:
        logger.error(f"Lỗi Gemini: {e}")
        return f"Lỗi xử lý ngôn ngữ nội bộ: {e}", None


async def handle_chat(request):
    """
    Nhận tin nhắn JSON từ Telegram Bot (Relay) và chuyển cho Agent xử lý.
    """
    try:
        data = await request.json()
        user_id = data.get("user_id")
        query = data.get("query", "")
        
        session_id = str(user_id)
        logger.info(f"Nhận request từ session {session_id}: {query}")
        
        # 1. Lưu tin của user vào Memory
        memory.add_message(session_id, "user", query)
        
        # 2. Load context
        history = memory.get_chat_history(session_id, limit=8) # Phân tích ngữ cảnh 8 lượt gần nhất

        # 3. Yêu cầu Gemini xử lý
        answer_text, fn_data = get_gemini_response_with_tools(query, history)

        response_payload = {}

        # 4. Thực thi Function Call nếu AI yêu cầu
        if answer_text == "INTENT_COMPARE" and fn_data:
            kwargs = json.loads(fn_data)
            dev_a = kwargs.get("device_a", "")
            dev_b = kwargs.get("device_b", "")
            
            logger.info("Thực thi Compare Agent theo lệnh của LLM...")
            # Gọi hàm compare_handler async (thao tác này có thể mất thời gian)
            md_text, xlsx_path = await compare_handler(dev_a, dev_b, session_id)
            
            final_text = f"Dưới đây là kết quả phân tích theo yêu cầu của bạn:\n\n<pre>{md_text}</pre>"
            response_payload = {
                "text": final_text,
                "file_path": xlsx_path
            }
            # Lưu câu trả lời thành công
            memory.add_message(session_id, "model", f"Tôi đã so sánh {dev_a} và {dev_b} và trả về file báo cáo.")
            
        else:
            # Câu trả lời thông thường
            response_payload = {
                "text": answer_text,
                "file_path": None
            }
            # Lưu tin trả về vào Memory
            if answer_text:
                 memory.add_message(session_id, "model", answer_text)

        return web.json_response(response_payload)
        
    except Exception as e:
        logger.error(f"Lỗi API: {e}")
        return web.json_response({"text": f"Lỗi nội bộ API Server: {e}", "file_path": None}, status=500)


app.router.add_post('/api/chat', handle_chat)

if __name__ == '__main__':
    logger.info("Khởi động Antigravity Headless API Server (Gemini + Memory) trên cổng 8081...")
    web.run_app(app, host='127.0.0.1', port=8081)
