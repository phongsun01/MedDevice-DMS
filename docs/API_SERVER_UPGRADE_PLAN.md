# API Server Upgrade and Memory Management Plan

## 1. Cơ chế hoạt động của "Memory" (Cách Antigravity nhớ lịch sử chat)

Để một AI Agent (như Antigravity) có thể "nhớ" được nội dung bạn vừa nói trước đó, API Server cần đóng vai trò là người quản lý **Ngữ cảnh (Context)**. LLM mặc định không có trạng thái (stateless), nghĩa là mỗi câu hỏi gửi đi đều độc lập. 

Cơ chế Memory trong ứng dụng của bạn sẽ hoạt động như sau:
* **Định danh phiên (Session/Chat ID):** Khi user nhắn tin trên Telegram, bot sẽ gửi kèm `chat_id` và `user_id` tới API Server.
* **Lưu trữ Lịch sử (Chat History Storage):** API Server sẽ lưu toàn bộ tin nhắn của User và câu trả lời của Agent vào sơ sở dữ liệu (sử dụng bảng SQLite cục bộ cho tốc độ cực cao, tại `storage/memory.db`).
* **Bơm ngữ cảnh (Context Injection):** Khi có một tin nhắn mới, API Server sẽ query DB để lấy ra *N tin nhắn gần nhất* (ví dụ 10 tin nhắn). Sau đó, nó gộp câu hỏi mới vào danh sách này và gửi toàn bộ mảng lịch sử đó lên LLM (Google Gemini). Nhờ đọc được cả mảng lịch sử (giống như đọc lại tin nhắn chat), AI sẽ hiểu được các đại từ thay thế (ví dụ: "Nó giá bao nhiêu?" -> "Nó" là máy Examion bạn vừa hỏi ở câu trước).

### Các tầng Memory đề xuất cho dự án:
1. **Short-term Memory (Bộ nhớ ngắn hạn - Session Logging):** Lưu lại 10-20 đoạn hội thoại (turns) gần nhất để đảm bảo tính liên tục của cuộc trò chuyện hiện tại. Quá độ dài này sẽ bị cắt đuôi bớt (sliding window) để tránh gửi quá giới hạn token của LLM.
2. **Long-term Memory (Bộ nhớ dài hạn - Vector DB):** (Tương lai) Khi user hỏi ngữ cảnh mới, hệ thống sẽ Semantic Search lấy ra mẩu nhớ cũ và đưa ẩn vào trong System Prompt.

## 2. Thay đổi kiến trúc API Server

### Tầng DB & Core
* **`core/memory.py`**: Class `MemoryManager` quản lý kết nối SQLite. Cung cấp các hàm `add_message`, `get_chat_history`, `clear_history`.

### Tầng API Server
* **`api_server.py`**: 
  - Tích hợp logic gọi SDK Gemini (`google-generativeai`).
  - Gắn lịch sử chat (`history_ctx`) vào Prompts kèm theo System Prompt để định tuyến Intent (Ý định).
  - Khai báo tool (Function Calling) để Gemini có thể gọi `compare_agent.py` nếu phát hiện cần so sánh.
  - Lưu kết quả trả về của AI vào DB.
