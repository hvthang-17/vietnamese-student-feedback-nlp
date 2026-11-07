# Báo cáo và evidence theo thời điểm

Đây là lịch sử thực hiện, không phải bảng tiến độ hiện hành. Xem [status](../status.md). Không cộng số tests hoặc đồng nhất latency giữa các report khác scope.

| Báo cáo 07/11/2026 | Nội dung / phạm vi |
| --- | --- |
| [Dataset và baseline](2026-11-07/execution-report-20261107.md) | Snapshot thật, EDA, calibration, metrics và lỗi baseline |
| [Review hai ZIP](2026-11-07/phobert-results-review-20261107.md) | Kiểm tra export GPU, tái tính metrics; chưa phải inference reload |
| [Audit giai đoạn](2026-11-07/project-stage-audit-20261107.md) | Các gate còn thiếu ở thời điểm audit, trước CPU/integration |
| [So sánh baseline/PhoBERT và chọn model](2026-11-07/model-selection-20261107.md) | Accuracy, macro/weighted F1 validation/test; per-class P/R/F1, confusion matrices test, chi phí và căn cứ lựa chọn; bổ sung evidence HTTP ở giai đoạn 6 |
| [API integration](2026-11-07/api-integration-20261107.md) | HTTP thật, SQLite tạm, failure atomicity và latency tuần tự |
| [UI giai đoạn 7](2026-11-07/ui-reports-stage7.md) | Pagination/date/matrix/PDF; giới hạn kiểm chứng ban đầu |
| [UI redesign](2026-11-07/ui-redesign.md) | Góc lắng nghe, build và Edge/CDP fixture checks |

Evidence gốc vẫn trong artifacts/runs và artifacts/reviews; không đổi hashes/metrics hoặc di chuyển checkpoint trong đợt tái cấu trúc docs. Kết quả test CLI dotenv riêng được ghi trong cuộc kiểm chứng cấu hình, không có full-suite report mới; xem status.
