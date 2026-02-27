# Use Cases — MedDevice DMS (v2.3.0)

> Tài liệu này mô tả các tình huống sử dụng thực tế của hệ thống, phân theo 2 nhóm người dùng:
> - **Quản trị viên (Admin):** Người quản lý kho tài liệu, có quyền thêm/sửa/xóa.
> - **Người dùng cuối (End User):** Nhân viên/lãnh đạo tra cứu thông tin.

---

## 🗂 Nhóm A: Quản lý Kho Tài Liệu (Admin via Telegram)

### UC-01: Upload file và phân loại tự động *(Option A — v2.3)*

**Kịch bản:** Admin nhận được file báo giá thiết bị mới từ đơn vị cung cấp.

```
Admin gửi file "arrieta60.pdf" vào Group Telegram
  ↓
Bot tải file về, gọi AI phân loại
  ↓
Bot hỏi: "Đề xuất: tech-arrieta-60-vi.pdf → sieu-am/arrieta-60/"
         [✅ Xác nhận] [✏️ Sửa] [❌ Huỷ]
  ↓
Admin: "đây là hợp đồng"
  ↓
Bot cập nhật: "contract-arrieta-60-vi.pdf → sieu-am/arrieta-60/"
         [✅ Xác nhận] [✏️ Sửa] [❌ Huỷ]
  ↓
Admin: ✅ Xác nhận
  ↓
Hệ thống: Rename + Move file + Cập nhật SurrealDB
  ↓
Bot: "✅ Đã phân loại và nạp vào hệ thống!"
```

---

### UC-02: Ra lệnh quét thư mục qua Bot *(Option A — v2.3)*

**Kịch bản:** Admin vừa copy nhiều file mới vào D:\MedicalData, muốn nạp vào hệ thống.

```
Admin: "Quét lại thư mục ct-scan giúp tôi"
  ↓
Bot: "Tôi đang chạy scan --dry-run trước..."
  ↓
Bot: "Tìm thấy 3 file mới: [danh sách]. Xác nhận nạp vào DB?"
  ↓
Admin: "Đồng ý"
  ↓
Hệ thống: scan thật → ghi DB
  ↓
Bot: "✅ Đã nạp 3 tài liệu mới. DB hiện có 228 docs."
```

---

### UC-03: Báo cáo thiếu tài liệu theo lệnh chat *(Option A — v2.3)*

**Kịch bản:** Chuẩn bị họp, cần kiểm tra thiết bị nào chưa có báo giá.

```
Admin: "Thiết bị nào chưa có hồ sơ báo giá?"
  ↓
Bot gọi CLI: python cli.py missing --doc-type price
  ↓
Bot: "⚠️ 5 thiết bị chưa có báo giá:
      - Somatom Go Now
      - DSA Azurion 7B20
      - ..."
     [📊 Xuất Excel] [📝 Lưu Wiki]
```

---

### UC-04: Đồng bộ Wiki sau khi cập nhật dữ liệu

**Kịch bản:** Sau khi nạp dữ liệu mới, cần cập nhật trang Wiki nội bộ.

```
Admin: "Sync wiki đi"
  ↓
Bot gọi: python cli.py wiki sync
  ↓
Bot: "✅ Đã cập nhật 12 trang Wiki. Xem tại: http://outline.internal/..."
```

---

## 🔍 Nhóm B: Tra cứu thông tin (End User via Telegram)

### UC-05: Tìm kiếm tài liệu theo ngôn ngữ tự nhiên

**Kịch bản:** Kỹ thuật viên cần tìm tài liệu hướng dẫn cấu hình cho máy CT Siemens.

```
User: "Cho tôi tài liệu cấu hình máy CT Somatom Go Now"
  ↓
Bot: "Tìm thấy 3 tài liệu:
      1. config-somatom-go-now-vi.pdf (2024-01-15)
      2. tech-somatom-go-now-en.pdf
      3. config-somatom-go-now-en.pdf
     [📥 Tải xuống] [🔗 Wiki]"
```

---

### UC-06: So sánh hai thiết bị

**Kịch bản:** Lãnh đạo cần so sánh 2 máy siêu âm để ra quyết định mua sắm.

```
User: "So sánh Arietta 50 và Arietta 750V cho tôi"
  ↓
Bot: "Đang phân tích..."
  ↓
Bot gửi bảng so sánh Markdown + file Excel
  ↓
User: "Arietta 750V có những điểm gì nổi bật hơn không?"
  ↓
Bot (nhớ ngữ cảnh): "Dựa vào bảng vừa so sánh, Arietta 750V nổi bật..."
```

---

### UC-07: Duyệt danh mục thiết bị

**Kịch bản:** Nhân viên mới muốn xem hệ thống đang quản lý loại máy nào.

```
User: /list
  ↓
Bot hiển thị menu Category:
  [🔬 Chẩn đoán hình ảnh] [💊 Điều trị] [🏥 Hỗ trợ lâm sàng]
  ↓
User chọn: Chẩn đoán hình ảnh
  ↓
Bot hiển thị Group: [CT Scan] [Siêu âm] [C-Arm] [MRI] [X-Quang]
  ↓
User chọn: CT Scan
  ↓
Bot liệt kê: Somatom Go Now | CT 128 Go Top | ...
  ↓
User chọn thiết bị → xem tài liệu
```

---

## ⚙️ Nhóm C: Vận hành Hệ Thống (Admin via CLI / Antigravity IDE)

### UC-08: Chuẩn hóa thư mục dữ liệu

```bash
# Xem trước
python cli.py normalize --dry-run

# Thực hiện
python cli.py normalize

# Sau đó nạp lại vào DB
python cli.py scan
```

### UC-09: Kiểm tra sức khỏe hệ thống trước demo

```bash
python cli.py health     # SurrealDB + Wiki OK?
python cli.py stats      # Tổng quan dữ liệu
python cli.py search "CT scan"  # Test tìm kiếm
```

### UC-10: Thêm thiết bị mới qua CLI

```bash
python cli.py device create \
  --name "Arietta 60" \
  --group "sieu-am" \
  --brand "Hitachi" \
  --model "Arietta 60"
```
