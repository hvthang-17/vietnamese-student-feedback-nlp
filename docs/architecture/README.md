# Kiến trúc và bản triển khai hiện tại

Đọc [system design](system-design.md), [API design](api-design.md) và [database design](database-design.md) cho sơ đồ, luồng xử lý, schema và lộ trình mở rộng. Đây là modular monolith; chưa có microservices, PostgreSQL hoặc queue.

## Backend component structure

```text
backend/app/
├── main.py                 create_app(settings, predictor), lifespan, routing, error/log context
├── __main__.py             serve / migrate commands
├── settings.py             Process environment và resource limits
├── domain/
│   ├── models.py           Enums, prediction contract, filter và write values
│   └── ports.py            Predictor và FeedbackStore protocols
├── api/
│   ├── dependencies.py     Auth, filter parsing, service dependency
│   ├── middleware.py       Request body limit trước parsing
│   ├── predictions.py      Single/batch HTTP adapters
│   ├── imports.py          Multipart adapter, chạy trong sync worker
│   ├── dashboard.py        List/detail/summary HTTP adapters
│   └── exports.py          CSV/PDF HTTP adapters
├── services/
│   ├── feedback.py         Predict và điều phối atomic persistence
│   ├── imports.py          CSV validation và partial row errors
│   └── reports.py          Bounded export, formula protection, PDF wrapping
├── repository.py           SQLiteFeedbackRepository implementation
├── database.py             Connection/transaction/lifecycle adapter
├── migrations.py           Append-only schema revisions
├── inference.py            Predictor factory và sklearn/demo adapter
├── phobert.py              Imported-run verification và PhoBERT predictor adapter
├── phobert_runtime.py      Lazy CPU runtime dùng chung evaluation/serving
├── schemas.py              Pydantic HTTP request/response contracts
└── labels.py, preprocessing.py, clock.py
```

Hướng phụ thuộc: HTTP → services → domain/ports; repository và inference là adapters. Chỉ app factory lắp các phần với nhau. Không có inference singleton/database path chốt lúc import. Model load diễn ra một lần trong lifespan, database connections theo operation.

## Frontend component structure

`frontend/src/main.jsx` mount React; App.jsx chọn trang bằng state. Pages Analyze/Dashboard/Import gọi API và ghép Header, Badge, PieChart; config.js giữ base URL và nhãn, styles.css giữ styling. Các endpoint và field cũ được giữ để UI local tiếp tục dùng. UI Góc lắng nghe có date filters, matrix và pagination, chưa có auth flow. Browser fixture checks không thay thế E2E checkpoint thật.

## Offline ML và dữ liệu

Workspace có topbar cố định và sidebar thu/mở. Thanh công cụ Dashboard cố định chỉ gồm nút lọc, số điều kiện và xuất file; các ô lọc nằm bên ngoài, cuộn theo trang để không che biểu đồ. Dashboard hiển thị đồng thời KPI, hai biểu đồ donut, ma trận và danh sách theo cùng bộ lọc, không chia chế độ xem. Riêng bảng phản hồi cuộn độc lập, giữ tiêu đề cột; phân trang ở phía trên với 10/20/50/100 dòng, đổi số dòng trả về trang 1. Khi đổi page/page_size với cùng filters, giữ dữ liệu và DOM bảng trong lúc tải, khóa điều khiển đang chờ và cập nhật nội dung khi response thành công; không gỡ bảng làm mất vị trí cuộn. Đổi filters mới reset dữ liệu, export không dùng dữ liệu thuộc filter cũ. Export dùng toàn bộ kết quả theo filters, không áp dụng page/page_size.

Dashboard dùng PieChart (SVG donut) cho phân bố cảm xúc/chủ đề, lấy số đếm từ summary API theo cùng bộ lọc. Chú giải hiển thị số lượng và tỷ trọng từng nhóm, tâm vòng tròn là tổng phản hồi; tập rỗng hiển thị vòng nền và hướng dẫn. Tỷ trọng này không phải confidence của model. Không có dependency chart bổ sung.

`ml/` dùng CLI và các package core/data/training/evaluation/deployment. Xem [ML workflow](../../ml/README.md). Snapshot trong data/processed, mỗi experiment trong artifacts/runs. API chỉ nạp artifact đã được chọn; không train khi nhận request. Production startup từ chối legacy artifact thiếu official-dataset provenance; development vẫn có thể dùng artifact cũ, không được coi đó là nghiệm thu chất lượng.

## Entry points và kiểm tra

- API: `uvicorn backend.app.main:app --reload` hoặc `python -m backend.app serve`.
- Migration: `python -m backend.app migrate`, với DATABASE_PATH đã được kiểm tra và backup khi có dữ liệu quan trọng.
- Frontend: `npm run dev` trong frontend.
- Tests: `python -B -m pytest tests -q -p no:cacheprovider` từ gốc. Các fixture tạo database tạm và predictor giả, không xóa database runtime.
- TestClient và atomic-file replacement có thể bị sandbox Windows chặn; phân biệt lỗi môi trường với lỗi test và chỉ chạy ngoài sandbox theo quyền được cấp.

Không có cam kết capacity/load test hoặc UI e2e trong bản này. Cấu hình môi trường và quy trình chạy ở README; hợp đồng machine-readable được sinh trực tiếp tại /openapi.json.
