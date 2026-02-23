<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# đưa ra workflow, nêu rõ nhiệm vụ từng thành phần

Workflow quản lý hồ sơ thiết bị y tế được thiết kế rõ ràng với Antigravity IDE làm trung tâm, SurrealDB lưu trữ, và Telegram giao tiếp từ xa.




## Workflow chi tiết

Quy trình theo thứ tự: User gửi tài liệu qua Telegram → Agent xử lý → Lưu/truy vấn DB → Cập nhật wiki → Phản hồi kết quả.

*(Flowchart minh họa đầy đủ với màu sắc phân biệt: xanh cho agent/DB, cam cho Telegram).*

## Nhiệm vụ từng thành phần

### Telegram Bot

- Nhận file/tài liệu từ user, forward vào Antigravity workspace qua webhook.[^1]
- Xử lý lệnh query (tìm kiếm/so sánh), gửi kết quả realtime (text/table/wiki link).[^2]


### Antigravity Agents

- Extract dữ liệu từ docs (NLP/Gemini), parse specs thiết bị.[^3]
- Index/search trong SurrealDB (full-text/graph queries).[^3]
- Generate so sánh (table diffs), update wiki pages tự động.[^4]


### SurrealDB

- Lưu hồ sơ (documents với fields: name, specs, docs), realtime sync.[^3]
- Query semantic/full-text cho tìm kiếm, graph cho quan hệ thiết bị.[^3]


### Wiki (Foam/Dendron extension)

- Hiển thị tổng quát (graph view hồ sơ), link docs, realtime từ DB.[^5]

Setup ban đầu: Prompt Antigravity "Build this workflow with SurrealDB + Telegram bot".[^6]

## 🛠 Lưu ý triển khai (Deployment Notes)

1. **Tương thích Box Drive**: Nếu chạy project trong thư mục đồng bộ Box Drive, cần thiết lập `set DOCKER_BUILDKIT=0` trong `setup.bat` để tránh lỗi đọc file.
2. **SurrealDB Storage**: Trong môi trường development, SurrealDB được cấu hình chạy `memory` mode để đạt hiệu năng cao nhất và tránh lỗi lock file trên Windows.
3. **Polling vs Webhook**: Hệ thống tự động nhận diện `WEBHOOK_URL`. Nếu chưa có tunnel (ngrok/cloudflare), Bot sẽ tự động chạy `polling` mode để bạn có thể test ngay lập tức.


<div align="center">⁂</div>

[^1]: https://www.reddit.com/r/google_antigravity/comments/1q31qxa/made_a_tool_to_control_my_ide_from_telegram/

[^2]: https://www.reddit.com/r/google_antigravity/comments/1qhocbz/presenting_antigravity_remote_work_from_literally/

[^3]: https://www.antigravityide.app/features

[^4]: https://www.theverge.com/news/822833/google-antigravity-ide-coding-agent-gemini-3-pro

[^5]: https://www.youtube.com/watch?v=P2lcCvt2RYw

[^6]: https://www.youtube.com/watch?v=gYvFsHd7Q7w

