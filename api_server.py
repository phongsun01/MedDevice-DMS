import os
import json
import logging
import subprocess
import shutil
from pathlib import Path
from aiohttp import web
from agents.compare_agent import compare_handler
from agents.normalize_agent import normalize_proposal, slugify
from core.memory import memory
from google import genai
from google.genai import types
from config import settings

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Antigravity-API")

app = web.Application()

# Khởi tạo Gemini Client (dùng cho Option B)
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# ─── Option B: System Prompt & Gemini Chat ───────────────────────────────────

SYSTEM_PROMPT = """Bạn là Antigravity Agent - hệ thống AI nội bộ quản lý tài liệu y tế (MedDevice DMS).
Nhiệm vụ của bạn là đọc tin nhắn của người dùng và lịch sử chat (nếu có), hiểu ngữ cảnh và trả lời.
Bạn có khả năng gọi hàm (function_calling) để thực hiện các nghiệp vụ đặc biệt nếu cần.
Nếu người dùng yêu cầu "so sánh thiết bị", bạn PHẢI gọi công cụ 'compare_devices_tool'.
Nếu chỉ hỏi đáp thông thường, bạn trả lời bằng tiếng Việt chuyên nghiệp, ngắn gọn.
"""

def get_gemini_response_with_tools(query: str, history_msgs: list) -> tuple[str, str | None]:
    compare_device_declaration = {
        "name": "compare_devices_tool",
        "description": "Gọi hàm này khi người dùng muốn so sánh thông số kỹ thuật giữa 2 thiết bị.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "device_a": {"type": "STRING", "description": "Tên dòng máy thứ nhất"},
                "device_b": {"type": "STRING", "description": "Tên dòng máy thứ hai"},
            },
            "required": ["device_a", "device_b"]
        }
    }
    contents = [
        types.Content(role=msg["role"], parts=[types.Part.from_text(text=msg["content"])])
        for msg in history_msgs
    ]
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=query)]))
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
        if response.function_calls:
            for fn_call in response.function_calls:
                if fn_call.name == "compare_devices_tool":
                    return "INTENT_COMPARE", json.dumps(fn_call.args)
        if response.text:
            return response.text, None
        return "Xin lỗi, tôi không thể xử lý yêu cầu lúc này.", None
    except Exception as e:
        logger.error(f"Lỗi Gemini: {e}")
        return f"Lỗi xử lý ngôn ngữ nội bộ: {e}", None


async def handle_chat(request):
    """Option B: Nhận tin nhắn, xử lý bằng Gemini + Memory."""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        query = data.get("query", "")
        session_id = str(user_id)
        logger.info(f"[Option B] session={session_id}: {query}")

        memory.add_message(session_id, "user", query)
        history = memory.get_chat_history(session_id, limit=8)
        answer_text, fn_data = get_gemini_response_with_tools(query, history)

        if answer_text == "INTENT_COMPARE" and fn_data:
            kwargs = json.loads(fn_data)
            dev_a, dev_b = kwargs.get("device_a", ""), kwargs.get("device_b", "")
            logger.info(f"Trigger compare_handler: {dev_a} vs {dev_b}")
            md_text, xlsx_path = await compare_handler(dev_a, dev_b, session_id)
            final_text = f"Dưới đây là kết quả phân tích:\n\n<pre>{md_text}</pre>"
            memory.add_message(session_id, "model", f"Đã so sánh {dev_a} và {dev_b}.")
            return web.json_response({"text": final_text, "file_path": xlsx_path})

        if answer_text:
            memory.add_message(session_id, "model", answer_text)
        return web.json_response({"text": answer_text, "file_path": None})

    except Exception as e:
        logger.error(f"Lỗi API chat: {e}")
        return web.json_response({"text": f"Lỗi nội bộ: {e}", "file_path": None}, status=500)


# ─── Option A: File Classification & Execution ───────────────────────────────

GEMINI_MD_PATH = Path(__file__).parent / "GEMINI.md"

def _call_gemini_cli(filename: str) -> dict | None:
    """
    Gọi gemini-cli non-interactive để phân loại file.
    Yêu cầu gemini-cli đã được cài và đăng nhập OAuth.
    """
    prompt = f'Classify this file for MedDevice DMS system. Filename: "{filename}". Return JSON only.'
    try:
        result = subprocess.run(
            ["gemini", "--yolo", "-p", str(GEMINI_MD_PATH), prompt],
            capture_output=True, text=True, timeout=30, encoding="utf-8"
        )
        output = result.stdout.strip()
        # Tách JSON ra khỏi output (có thể có text thừa)
        start = output.find("{")
        end = output.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(output[start:end])
        logger.error(f"gemini-cli output không phải JSON: {output[:200]}")
        return None
    except subprocess.TimeoutExpired:
        logger.error("gemini-cli timeout")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error từ gemini-cli: {e}")
        return None
    except FileNotFoundError:
        logger.error("gemini-cli chưa được cài. Chạy: npm install -g @google/generative-ai-cli")
        return None


async def handle_classify_file(request):
    """
    Option A: Nhận thông tin file → gọi gemini-cli → trả về đề xuất phân loại.
    POST /api/classify_file
    Body: { "filename": "arrieta60.pdf" }
    """
    try:
        data = await request.json()
        filename = data.get("filename", "")
        if not filename:
            return web.json_response({"error": "Thiếu filename"}, status=400)

        logger.info(f"[Option A] classify_file: {filename}")

        if settings.AGENT_MODE == "A":
            # Gọi gemini-cli (yêu cầu đăng nhập OAuth)
            ai_result = _call_gemini_cli(filename)
        else:
            # Fallback: dùng Gemini API trực tiếp (Option B mode)
            ai_result = None

        if not ai_result:
            # Fallback sang Gemini API nếu gemini-cli thất bại
            try:
                with open(GEMINI_MD_PATH, "r", encoding="utf-8") as f:
                    ctx = f.read()
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"{ctx}\n\nFilename: {filename}\nReturn JSON only."
                )
                raw = response.text.strip()
                start = raw.find("{")
                end = raw.rfind("}") + 1
                ai_result = json.loads(raw[start:end]) if start >= 0 else None
            except Exception as e:
                logger.error(f"Fallback Gemini API failed: {e}")
                return web.json_response({"error": f"Không thể phân loại: {e}"}, status=500)

        if not ai_result or not ai_result.get("device"):
            return web.json_response({
                "error": "Không xác định được thiết bị từ tên file",
                "ai_raw": ai_result
            }, status=422)

        # Tạo đề xuất đầy đủ
        proposal = normalize_proposal(
            original_filename=filename,
            doc_type=ai_result.get("doc_type", "other"),
            device_slug=ai_result.get("device", ""),
            device_display=ai_result.get("device_display", ai_result.get("device", "")),
            category=ai_result.get("category", ""),
            group=ai_result.get("group", ""),
            lang=ai_result.get("lang", "vi"),
        )
        proposal["confidence"] = ai_result.get("confidence", 0)
        proposal["reason"] = ai_result.get("reason", "")

        return web.json_response(proposal)

    except Exception as e:
        logger.error(f"Lỗi classify_file: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_execute_task(request):
    """
    Option A: Thực thi sau khi user xác nhận — rename file, move vào đúng thư mục, chạy scan.
    POST /api/execute_task
    Body: {
        "tmp_path": "C:/tmp/abc/arrieta60.pdf",
        "target_dir": "D:/MedicalData/thiet-bi-chan-doan-hinh-anh/sieu-am/arietta-60",
        "suggested_filename": "tech-arietta-60-vi.pdf",
        "device": "arietta-60",
        "session_id": "12345"
    }
    """
    try:
        data = await request.json()
        tmp_path = Path(data.get("tmp_path", ""))
        target_dir = Path(data.get("target_dir", ""))
        new_filename = data.get("suggested_filename", "")
        device_slug = data.get("device", "")
        session_id = str(data.get("session_id", ""))

        if not tmp_path.exists():
            return web.json_response({"error": f"File tạm không tồn tại: {tmp_path}"}, status=400)

        # 1. Tạo thư mục nếu chưa có
        target_dir.mkdir(parents=True, exist_ok=True)

        # 2. Move và rename file
        dest = target_dir / new_filename
        shutil.move(str(tmp_path), str(dest))
        logger.info(f"[Option A] Đã move: {tmp_path} → {dest}")

        # 3. Chạy scan_agent cho thư mục thiết bị
        try:
            from db import client as db_client
            await db_client.connect()
            from agents.scan_agent import scan_directory
            report = await scan_directory(base_dir=str(target_dir.parent.parent), dry_run=False)
            docs_added = report.get("processed", 0)
            logger.info(f"[Option A] Scan xong: {docs_added} docs processed")
        except Exception as scan_err:
            logger.warning(f"Scan sau khi move thất bại (không nghiêm trọng): {scan_err}")
            docs_added = 0

        return web.json_response({
            "success": True,
            "dest": str(dest),
            "docs_added": docs_added,
            "message": f"✅ Đã phân loại: {new_filename} → {target_dir.name}/"
        })

    except Exception as e:
        logger.error(f"Lỗi execute_task: {e}")
        return web.json_response({"error": str(e)}, status=500)


# ─── Routes ──────────────────────────────────────────────────────────────────

app.router.add_post('/api/chat', handle_chat)
app.router.add_post('/api/classify_file', handle_classify_file)
app.router.add_post('/api/execute_task', handle_execute_task)

if __name__ == '__main__':
    logger.info(f"Khởi động Antigravity API Server (AGENT_MODE={settings.AGENT_MODE}) trên cổng 8081...")
    web.run_app(app, host='127.0.0.1', port=8081)
