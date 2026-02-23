# MedDevice DMS

**Hệ thống Quản lý Hồ sơ Thiết bị Y tế (Medical Device Document Management System)**

MedDevice DMS là giải pháp quản lý hồ sơ kỹ thuật, thông số và so sánh thiết bị y tế toàn diện dựa trên nền tảng AI và SurrealDB. Hệ thống cho phép người dùng tương tác từ xa qua Telegram Bot và tra cứu dữ liệu dạng Wiki.

## 🌟 Tính năng chính

- **Cấu trúc phân cấp**: Quản lý theo Category > Group > Device với các nhóm tài liệu chuẩn hóa.
- **Tìm kiếm AI**: Hỗ trợ tìm kiếm toàn văn (full-text) và ngữ nghĩa trong nội dung file PDF/Word.
- **So sánh tự động**: Tự động trích xuất và so sánh thông số kỹ thuật giữa các thiết bị.
- **Giao diện đa kênh**: 
  - **Telegram Bot**: Nhận file, tra cứu, tìm kiếm và điều khiển hệ thống từ xa.
  - **Wiki (Outline)**: Trang tra cứu tổng quát, tự động cập nhật từ cơ sở dữ liệu.
- **Lưu trữ bảo mật**: Hỗ trợ lưu trữ local, Google Drive hoặc S3.

## 🛠 Công nghệ sử dụng

- **Database**: [SurrealDB](https://surrealdb.com/) (Multi-model graph database)
- **AI/LLM**: Google Gemini (via Antigravity Agents)
- **Interface**: Python Telegram Bot
- **Wiki**: Outline (self-hosted)
- **Runtime**: Antigravity IDE

## 📂 Cấu trúc thư mục

- `docs/`: Tài liệu dự án (PRD, Implementation Plan).
- `src/`: Mã nguồn bot và các agents xử lý.
- `schema/`: Định nghĩa SurrealDB schema và migrations.
- `storage/`: Thư mục lưu trữ file (local).

## 🚀 Bắt đầu

Dự án đang trong giai đoạn phát triển ban đầu (v0.1.0).

1. Clone dự án: `git clone https://github.com/phongsun01/MedDevice-DMS`
2. Cấu hình file `.env` (xem `.env.example`)
3. Chạy `docker-compose up -d` để khởi động SurrealDB và Outline.
