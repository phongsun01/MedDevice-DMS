# Antigravity IDE — Vai trò Agent trong Dự án MedDevice DMS

## 🤖 Antigravity là gì?

**Antigravity** là một AI Coding Agent được nhúng trực tiếp vào môi trường phát triển (IDE). Thay vì chỉ trả lời câu hỏi đơn thuần, Antigravity chủ động **tư duy, lập kế hoạch, triển khai code và vận hành hệ thống** như một kỹ sư phần mềm thực thụ — ngay trong IDE của bạn.

---

## 🏗 Vai trò trong Dự án MedDevice DMS

Dự án này được xây dựng **100% thông qua Antigravity**, từ ý tưởng đến hệ thống đang chạy. Antigravity đảm nhiệm toàn bộ vòng đời phát triển:

### 1. Giai đoạn Lập kế hoạch (Planning)
- **Phân tích yêu cầu**: Antigravity đặt câu hỏi Socratic để làm rõ mục tiêu trước khi code bất kỳ dòng nào.
- **Soạn PRD và Vibe Prompts**: Tự soạn thảo Product Requirements Document và Vibe Prompts chi tiết.
- **Tạo Implementation Plan**: Tự xây dựng kế hoạch kiến trúc có phân rã rõ ràng theo từng module.

### 2. Giai đoạn Triển khai (Execution)
- **Viết code toàn bộ stack**: Database schema (SurrealDB), AI agents (Gemini), Telegram Bot (aiogram), Wiki integration (Outline API), Docker Compose.
- **Tự Debug**: Phát hiện và sửa lỗi qua nhiều lần thử nghiệm (SurrealDB v3 syntax, RecordID format, module dependencies).
- **Quản lý file**: Tạo cấu trúc thư mục, viết `.gitignore`, `.env.example`, `setup.bat`, `QUICKSTART.md`.
- **Chạy lệnh terminal**: Trực tiếp chạy `docker`, `git`, `python`, `pip` để verify từng bước.

### 3. Giai đoạn Vận hành (Operations)
- **Kiểm tra Docker**: Theo dõi container log, phát hiện và khắc phục cấu hình Outline Wiki (`SECRET_KEY`).
- **Bảo mật**: Tự rà soát `.gitignore`, xóa file `.env` nhạy cảm khỏi GitHub history.
- **Import dữ liệu**: Viết và chạy script `import_local.py` để nạp 486 tài liệu vào hệ thống.
- **Release Management**: Tự quyết định version, tạo tag, viết changelog, push GitHub.

---

## 💡 Cách Antigravity hoạt động khác với AI thông thường

| Tiêu chí | AI Chat thường | Antigravity Agent |
|---|---|---|
| **Giao tiếp** | Chỉ trả lời văn bản | Thực thi lệnh thật trên hệ thống |
| **Phạm vi** | 1 câu hỏi → 1 câu trả lời | Điều phối nhiều công việc song song |
| **Bộ nhớ** | Quên sau phiên chat | Lưu trữ Knowledge Items & Artifacts |
| **Lập kế hoạch** | Không có | Tạo `task.md`, `implementation_plan.md` |
| **Debug** | Chỉ gợi ý | Tự chạy lại, đọc log, sửa code |
| **Git** | Hướng dẫn lệnh | Tự commit, tag, push |
| **Quyết định kỹ thuật** | Giải thích | Chọn stack, đề xuất cấu trúc tối ưu |

---

## 📂 Artifacts được tạo bởi Antigravity

Trong suốt dự án, Antigravity đã tạo và duy trì các tài liệu sau:

```
brain/<conversation-id>/
├── task.md              # Checklist công việc theo thời gian thực
├── implementation_plan.md  # Kế hoạch kiến trúc chi tiết
└── walkthrough.md       # Báo cáo kết quả và proof-of-work
```

Ngoài ra, trực tiếp trong codebase:
```
docs/
├── PRD.md               # Product Requirements Document
└── VIBE_PROMPTS.md      # Vibe Prompts cho từng module
QUICKSTART.md            # Hướng dẫn 5 bước khởi động
README.md                # Tài liệu kỹ thuật dự án
```

---

## 🔮 Phương pháp làm việc: Socratic Gate

Trước khi triển khai bất kỳ tính năng mới nào, Antigravity áp dụng **Socratic Gate** — đặt tối thiểu 3 câu hỏi chiến lược để tránh build sai. Ví dụ, khi bắt đầu dự án này, Antigravity đặt câu hỏi:

> *"Dữ liệu thiết bị sẽ được cập nhật thường xuyên không? Ai là người dùng cuối — kỹ sư hay lãnh đạo? Tìm kiếm cần hỗ trợ tiếng Việt không có dấu không?"*

Câu trả lời của bạn định hình toàn bộ kiến trúc: chọn SurrealDB (graph + full-text), Telegram Bot (remote access), Outline Wiki (không cần code frontend).

---

> *"Antigravity không phải là công cụ — đó là người đồng hành trong quá trình xây dựng phần mềm."*
