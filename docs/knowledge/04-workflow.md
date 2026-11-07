# 04. Quy trình nghiên cứu và triển khai

[Chỉ mục](README.md) · [Quy trình NLP chi tiết](../workflows/nlp-processing-workflow.md) · [ML workflow thực thi](../../ml/README.md)

```text
Prepare (official snapshot + commit + checksum)
    ↓
EDA (measured distributions, lengths, duplicate report)
    ↓
Train baseline / optional PhoBERT (new isolated run)
    ↓
Validation selection → final test metrics
    ↓
CPU benchmark baseline → review → explicit promote → restart API
```

## Vai trò từng bước

Prepare là ranh giới giữa tải dữ liệu và huấn luyện: các model dùng cùng snapshot, không tải lại một nguồn thay đổi theo thời gian. Hash kiểm tra tính toàn vẹn cục bộ; provenance vẫn cần nguồn đáng tin cậy. Độ trùng exact text được báo cáo, không tự sửa split chuẩn.

EDA tạo số đo thật. Có thể kiểm định schema/counts của cả ba split, nhưng chỉ khám phá train để quyết định đặc trưng; không đọc lỗi test để lặp tuning.

Training tạo thư mục run mới. Baseline chọn cấu hình bằng validation rồi hiệu chuẩn cả vectorizer/classifier bên trong CV. PhoBERT dùng cùng dữ liệu, checkpoint pin, PyVi và early stopping. Hai task được train riêng. Mỗi run ghi config thực dùng, environment, nguồn dữ liệu và trạng thái.

Evaluation dùng metric từng lớp và macro F1, không chỉ accuracy. File predictions lưu nhãn theo thứ tự snapshot để hỗ trợ phân tích lỗi. Test được dùng sau khi chốt cấu hình; không tuyên bố lần chạy lại test là đánh giá độc lập nếu đã dùng nó để cải tiến.

Có benchmark CPU cho baseline và joint PhoBERT, cùng benchmark HTTP/SQLite opt-in. Phân biệt phạm vi inference và toàn request; xem [ML workflow](../../ml/README.md) và [kết quả](../status.md). CLI promote chỉ hỗ trợ baseline; PhoBERT chọn imported run qua cấu hình adapter.

Promote là bước riêng, có kiểm tra checksum và ngưỡng nghiệm thu. Model API không bị thay khi train. Đây chưa phải hệ thống deployment/rollback; restart API sau khi thay artifact.

## Thực hiện lại

Tất cả commands, cấu trúc thư mục, output và xử lý lỗi được duy trì tại [ml/README.md](../../ml/README.md). Dùng tên snapshot/run mới khi cần bắt đầu lại; giữ `data/feedback.db` và kết quả lịch sử. Không có synthetic fallback trong pipeline mới.

Lịch sử baseline F1=1,0 từ canonical_local_seed và EDA cũ không phải bằng chứng cho dataset thật. Chúng được giữ nguyên để truy vết; pipeline mới không đọc chúng.
