# MedDevice DMS - Hệ thống Skill & Lệnh (Capabilities)

Tài liệu này tổng hợp các khả năng xử lý của Agents, các lệnh điều khiển qua Bot và CLI, cũng như các quy trình làm việc (Workflows) có sẵn trong hệ thống.

## 🤖 1. Các Skills (AI Agents)
Vị trí: `agents/`

Hệ thống sử dụng các Agent chuyên biệt để xử lý từng nhiệm vụ:
- **scan_agent.py**: Quét cấu trúc thư mục, phát hiện thiết bị và tài liệu mới.
- **parse_agent.py**: Trích xuất dữ liệu từ PDF/Word, tích hợp Vision để đọc các bản scan chất lượng thấp.
- **search_agent.py**: Xử lý tìm kiếm thông minh, semantic search và lọc kết quả.
- **compare_agent.py**: Phân tích thông số kỹ thuật (Specs) và lập bảng so sánh.
- **wiki_agent.py**: Đồng bộ hóa dữ liệu tự động với Outline Wiki.

## ⚡ 2. Slash Commands (Telegram Bot)
Các lệnh tương tác trực tiếp qua Telegram:
| Lệnh | Mô tả |
|---|---|
| `/start` | Hiển thị menu chính và hướng dẫn sử dụng. |
| `/list` | Duyệt danh mục thiết bị theo cấp độ: Category > Group > Device. |
| `/search <từ khóa>` | Tìm kiếm thông minh trong toàn bộ kho tài liệu. |
| `/add` | Quy trình (wizard) để thêm thiết bị mới từ xa. |
| `/wiki` | Cung cấp link truy cập nhanh hệ thống Wiki (Outline). |

## 🛠 3. CLI Commands (`cli.py`)
Công cụ dòng lệnh dành cho quản trị viên:
- `python cli.py stats`: Thống kê tổng quan số lượng thiết bị, file và dung lượng.
- `python cli.py scan`: Quét thư mục `storage/files/` để nạp dữ liệu vào Database.
- `python cli.py health`: Kiểm tra trạng thái kết nối Database, Wiki và Bot.
- `python cli.py wiki sync`: Đồng bộ dữ liệu hiện có lên trang Wiki.
- `python cli.py compare <A> <B>`: So sánh chi tiết thông số giữa hai thiết bị.

## 📜 4. Vibe Prompts (Workflows)
Vị trí: `docs/VIBE_PROMPTS.md`

Hệ thống tích hợp 13 quy trình làm việc chuẩn (Prompt 0 - 12) giúp Agent Antigravity giải quyết các tác vụ phức tạp:
- **Normalize**: Chuẩn hóa tên thư mục và xử lý trùng lặp.
- **Bulk Import**: Quy trình nạp dữ liệu hàng loạt an toàn.
- **Missing Check**: Phát hiện thiết bị thiếu hồ sơ/báo giá.
- **Health Check & Fix**: Tự động sửa lỗi dữ liệu (orphan records).
- **Onboard**: Quy trình nạp thiết bị mới từ folder vừa tạo.

---
*Tài liệu được khởi tạo bởi Antigravity vào ngày 26/02/2026.*
