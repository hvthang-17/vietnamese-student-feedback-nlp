# Cẩm nang đề tài phân loại phản hồi sinh viên tiếng Việt

Bộ tài liệu dành cho thành viên mới, người viết báo cáo và người trình bày đồ án. Đọc theo thứ tự dưới đây; mỗi chương nối kiến thức với mã nguồn đang có.

| Chương | Nội dung | Kết quả sau khi đọc |
| --- | --- | --- |
| [01 — Tổng quan](01-overview.md) | Bài toán, dữ liệu, phạm vi | Giải thích hệ thống làm gì |
| [02 — Kiến thức nền](02-foundations.md) | NLP tiếng Việt, học có giám sát, biểu diễn văn bản | Hiểu dữ liệu đi vào mô hình thế nào |
| [03 — Mô hình](03-models.md) | TF-IDF, SVM, calibration, Transformer và PhoBERT | Giải thích lựa chọn và giới hạn mô hình |
| [04 — Quy trình](04-workflow.md) | Dữ liệu → thí nghiệm → triển khai | Thực hiện công việc theo thứ tự có thể kiểm chứng |
| [05 — Đánh giá](05-evaluation.md) | Metrics, leakage, phân tích lỗi | Đọc kết quả đúng và tránh kết luận quá mức |
| [06 — Hệ thống và thuyết trình](06-system-and-presentation.md) | API, vận hành, dàn ý và câu hỏi bảo vệ | Liên hệ nghiên cứu với sản phẩm demo |

## Quy trình NLP chi tiết

Đọc [quy trình xử lý NLP từng bước](../workflows/nlp-processing-workflow.md) để hiểu đầu vào/đầu ra, ví dụ, mục đích và điều kiện hoàn thành từ kiểm định dữ liệu đến suy luận online.

## Quy ước

- **Hiện có**: mô tả implementation; trạng thái nghiệm thu và kết quả phải xem [status](../status.md).
- **Đề xuất**: công việc cần bổ sung, chưa được tài liệu này triển khai.
- Ví dụ câu, xác suất và phép tính được ghi là minh họa khi không phải kết quả thí nghiệm.
- Tài liệu không thay thế việc chạy thí nghiệm trên UIT-VSFC thật.

Các tài liệu liên quan: [kiến trúc](../architecture/README.md), [định dạng artifact](../architecture/artifact_and_metrics_format.md), [API](../architecture/api-examples.md), [Colab](../workflows/colab_training_guide.md), [PRD](../../tasks/prd-vietnamese-student-feedback-nlp.md).

## Evidence thực hiện

[Báo cáo dataset và baseline thực tế](../reports/2026-11-07/execution-report-20261107.md) · [Kế hoạch/trạng thái](../../tasks/implementation-plan.md) · [Handoff GPU](../workflows/colab_training_guide.md).
