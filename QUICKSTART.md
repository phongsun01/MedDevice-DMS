# ⚡ MedDevice DMS - Quickstart Guide

Chào mừng bạn đến với hệ thống Quản lý Thiết bị Y tế! Đây là 5 bước để bạn bắt đầu ngay lập tức.

## 1. Cấu hình ban đầu
Đảm bảo file `.env` đã có:
- `TELEGRAM_BOT_TOKEN`: Lấy từ @BotFather
- `GEMINI_API_KEY`: Lấy từ [Google AI Studio](https://aistudio.google.com/)

## 2. Khởi động hạ tầng
Mở terminal tại thư mục dự án và chạy:
```powershell
.\setup.bat
```
*Đợi Docker Desktop khởi động xong các container (khoảng 30s-1p).*

## 3. Thiết lập Wiki (Quan trọng)
1. Mở trình duyệt truy cập: `http://localhost:3000`
2. Tạo Workspace và tài khoản Admin.
3. Vào **Settings** (ở góc dưới bên trái) > **API Tokens**.
4. Chọn **Create Token**, đặt tên và sao chép mã Token.
5. Dán mã này vào `OUTLINE_API_TOKEN` trong file `.env`.

## 4. Nạp dữ liệu từ thư mục có sẵn
Nếu bạn có sẵn hồ sơ trong `storage/files`, hãy chạy:
```powershell
python import_local.py
```
*Script này sẽ nạp thiết bị vào Database và tạo trang Wiki tương ứng.*

## 5. Bắt đầu sử dụng Bot
Chạy Bot bằng lệnh:
```powershell
python main.py
```
Mở Telegram, gõ `/start` và bắt đầu tra cứu!

---
> [!TIP]
> Để hệ thống chạy nền vĩnh viễn, bạn có thể chạy `docker start meddevicedms-bot-1` thay vì chạy `python main.py` thủ công.
