# Phân loại phản hồi sinh viên tiếng Việt

Góc lắng nghe phân loại mỗi phản hồi thành một cảm xúc và một chủ đề bằng hai classifier độc lập. Dữ liệu nghiên cứu là UIT-VSFC; hệ thống dùng FastAPI, SQLite và React, so sánh TF-IDF/SVM với PhoBERT.

## Bắt đầu

- [Mục lục tài liệu](docs/README.md): chọn đúng tài liệu theo mục đích.
- [Trạng thái hiện tại](docs/status.md): đã làm gì, evidence nào có và gate nào còn mở.
- [Chạy demo](docs/guides/demo.md): hướng dẫn hiện hành, thay cho các chuỗi biến môi trường thủ công.
- [Cài môi trường](docs/guides/setup.md): dành cho máy chưa có dependencies/checkpoints.

Với môi trường và hai checkpoint đã có, mở hai PowerShell từ repository root:

```powershell
.\scripts\demo.ps1 backend
```

```powershell
.\scripts\demo.ps1 frontend
```

Mở http://localhost:5173; API docs tại http://127.0.0.1:8000/docs. Launcher chọn PhoBERT theo [config/demo.env](config/demo.env), dùng database demo riêng. Backend default khi chạy ngoài launcher vẫn là sklearn; không dùng artifact legacy để tuyên bố chất lượng UIT-VSFC thật. Biến môi trường sẵn có ưu tiên hơn file; nên dùng terminal mới.

## Điều hướng dự án

| Mục đích | Tài liệu |
| --- | --- |
| Phạm vi, nhãn và tiêu chí | [PRD](tasks/prd-vietnamese-student-feedback-nlp.md) |
| Kiến trúc, API, database | [Architecture](docs/architecture/README.md) |
| Lý thuyết NLP và mô hình | [Knowledge](docs/knowledge/README.md) |
| Quy trình train/evaluate | [ML workflow](ml/README.md) |
| Protocol nghiên cứu | [Experiment protocol](tasks/experiment-protocol.md) |
| Kết quả theo thời điểm | [Reports](docs/reports/README.md) |
| Hướng dẫn coding agent | [AGENTS.md](AGENTS.md) |

Tài liệu lịch sử/synthetic được đánh dấu riêng, không dùng thay kết quả chính thức. Điều khoản dataset ngoài mục đích học thuật còn cần xác minh; không dùng dự đoán để đánh giá/kỷ luật cá nhân.
