# Tài liệu dự án

Đọc [trạng thái hiện tại](status.md) để biết dự án đang ở đâu, hoặc [chạy demo](guides/demo.md) để sử dụng ngay.

Để viết báo cáo và giải thích quyết định chọn mô hình: đọc [so sánh baseline và PhoBERT](reports/2026-11-07/model-selection-20261107.md). Có bảng metrics, confusion matrices, chi phí và phân biệt lựa chọn demo với nghiệm thu production.

## Bản đồ tài liệu

| Khu vực | Vai trò | Điểm bắt đầu |
| --- | --- | --- |
| guides/ | Hướng dẫn vận hành hiện hành | [Demo](guides/demo.md), [setup](guides/setup.md), [PhoBERT nâng cao](guides/phobert-api-guide.md) |
| architecture/ | Mô tả implementation và hợp đồng | [Cấu trúc code](architecture/README.md), [system](architecture/system-design.md), [API](architecture/api-design.md), [DB](architecture/database-design.md), [ví dụ API](architecture/api-examples.md), [artifact](architecture/artifact_and_metrics_format.md) |
| workflows/ | Phương pháp và quy trình thực hiện | [NLP từng bước](workflows/nlp-processing-workflow.md), [Colab/Kaggle](workflows/colab_training_guide.md), [ML CLI](../ml/README.md) |
| knowledge/ | Kiến thức nền, giải thích và thuyết trình | [Cẩm nang](knowledge/README.md) |
| reports/ | Evidence và báo cáo tại từng thời điểm | [Danh mục báo cáo](reports/README.md) |
| archive/ | Kết quả cũ/synthetic, không dùng nghiệm thu | [Legacy](archive/README.md) |
| tasks/ (ngoài docs) | Yêu cầu, protocol và thứ tự công việc | [PRD](../tasks/prd-vietnamese-student-feedback-nlp.md), [plan](../tasks/implementation-plan.md), [protocol](../tasks/experiment-protocol.md) |

## Quy tắc đồng bộ

1. **Trạng thái chỉ ở [status.md](status.md).** README và plan dẫn link, không sao chép một bảng tiến độ khác.
2. Guides/architecture mô tả code hiện hành; ghi rõ phần đề xuất chưa triển khai. Knowledge giải thích phương pháp, không tự duy trì kết quả thực nghiệm riêng.
3. Reports giữ số liệu/scope của lần chạy; “chưa có” hoặc “bước tiếp theo” trong report chỉ đúng tại thời điểm đó. Không sửa lịch sử thành kết quả hiện tại.
4. Archive không phải benchmark thật. Artifacts/checkpoints/data là dữ liệu thực thi ngoài bộ tài liệu; không di chuyển hoặc xóa để sắp xếp docs. Thư mục docs/data đang có dữ liệu runtime cũ được giữ nguyên, không dùng làm nơi lưu tài liệu mới.
5. Khi thay code: cập nhật guide/contract liên quan; khi có evidence mới: thêm report, cập nhật status. Ghi command thực chạy, scope/hardware và giới hạn; không cộng số test ở các lần chạy thành một kết quả full suite.
6. Sau khi đổi đường dẫn: sửa cả link Markdown và đường dẫn được nhắc trong prose/code blocks. Kiểm tra file/anchor local; không cần train/build/test ứng dụng cho thay đổi chỉ có tài liệu.

## Thứ tự đọc đề xuất

Người chạy demo: guides/demo → status. Người làm nghiên cứu: PRD → knowledge → NLP workflow → protocol → ML CLI → reports. Người phát triển: architecture → API/DB → AGENTS → status.
