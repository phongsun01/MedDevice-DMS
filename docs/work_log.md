# Nhật ký công việc (Work Log)

## 2026-02-27: Khôi phục và chuẩn hóa cơ sở dữ liệu
- **Vấn đề**: Các thư mục bị lồng nhau (`ct-scan/ct-scan`), mất thông tin thiết bị, dữ liệu SurrealDB bị trống sau khi quét.
- **Phân tích**:
  - Script chuẩn hóa (`normalize_data_v2.py`) bị lỗi nhận diện cấp độ thư mục khi có các thư mục trung gian như `chung` hay `other-group`.
  - Schema SurrealDB yêu cầu các trường không bắt buộc (như `metadata`, `specs`), dẫn đến việc `INSERT` bị từ chối ngầm, làm dữ liệu không vào DB.
  - Client Python SurrelDB (`db/client.py`) có lỗi khi xử lý ID chứa dấy hai chấm (`:`) trong lệnh `create`. Cụ thể là lưu sai ID.
- **Hành động đã thực hiện**:
  - Viết lại logic `infer_hierarchy` trong `scan_agent.py` và `normalize_data_v2.py`.
  - Cập nhật Data: Normalize lại toàn bộ 228 files từ `D:\MedicalData` đưa vào đúng thư mục cấp độ thiết bị, xoá bỏ các folder trung gian.
  - Cập nhật `db/schema.surql`: Chuyển các trường `metadata`, `specs`, `doc_type` thành dạng `option<object>`/`option<string>`.
  - Cập nhật `agents/scan_agent.py`: Sử dụng `RecordID` thay vì chuỗi cho các Relation (liên kết khóa ngoại).
  - Đang debug tại sao Categories và phần lớn Groups/Devices chưa xuất hiện đầy đủ trong DB (Hiển thị Categories: 0, Groups: 3, Devices: 3 dù log chạy mượt). Đang kiểm tra lỗi format ID.
  - **Phát hiện 1**: Container Docker chạy `surrealdb` sử dụng engine `memory` dẫn đến xoá sạch data sau mỗi lần khởi động. Đã sửa trong `docker-compose.yml` thành `rocksdb:///data` cấu hình volume tuyệt đối đính kèm với persistent `/data` storage. Và cấp quyền `user: root`.
  - **Phát hiện 2**: DB Python Client `db/client.py` dính lỗi syntax query khi truyền chuỗi ID chứa ký tự nối `-` (VD: `category:thiet-bi-chuyen-dung`), SurrealDB engine hiểu lầm dấu gạch nối là **phép toán trừ** ("Cannot perform subtraction").
  - Đã patch lại Client: Dùng object `RecordID(table, id)` để bọc an toàn các ID chuỗi.
- **Kết quả cuối cùng**:
  - Quét lại toàn bộ 225 Documents thành công không có lỗi.
  - Thành công đẩy đủ Database Metrics: `Categories: 8, Groups: 17, Devices: 68, Documents: 225`. Toàn bộ dữ liệu DMS Hierarchy v2.1.1 đã sống lại.
