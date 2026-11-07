# Trạng thái hiện tại — đối chiếu ngày 07/11/2026

**Vị trí hiện tại: giai đoạn 7 đang chờ nghiệm thu đầy đủ; giai đoạn 8 chưa hoàn tất.** Nghiên cứu và API đã có evidence, UI đã redesign và kiểm chứng bằng fixtures.

Đây là nguồn trạng thái duy nhất. Không chạy lại test/train/benchmark trong lần đồng bộ tài liệu này; các con số là evidence của những lần chạy đã lưu, không phải kết quả mới.

Nguồn yêu cầu: [PRD](../tasks/prd-vietnamese-student-feedback-nlp.md), [NLP workflow](workflows/nlp-processing-workflow.md). Protocol thực nghiệm đã được chốt trong [experiment-protocol.md](../tasks/experiment-protocol.md). Thời hạn và nhân lực chưa được xác định; không gán lịch hoàn thành cố định.

| Giai đoạn | Mục tiêu / đầu ra | Điều kiện nghiệm thu | Trạng thái thực tế |
| --- | --- | --- | --- |
| 0. Yêu cầu và protocol | Chốt bài toán, labels, phạm vi, quality/latency và protocol | Có PRD, tiêu chí kiểm chứng và protocol trước thí nghiệm | Có PRD/protocol; chưa có bảng truy vết nghiệm thu đủ từng yêu cầu |
| 1. Kiến trúc và môi trường | API/schema/boundaries, runtime, quy trình test | Có thiết kế và code/test kiểm chứng; ghi environment thực tế | Có system/API/DB design, app factory; Regression có evidence 77 tests đạt; test CLI dotenv riêng 1 passed, không cộng thành một lần full suite 78 tests, frontend build có evidence trước đó. Môi trường CPU PhoBERT riêng đã chạy; dependency lock/Git/CI chưa hoàn chỉnh |
| 2. Dữ liệu và EDA | Official snapshot, revision/hashes, validation và thống kê | Đúng 11.426/1.583/3.166 mẫu; label/schema hợp lệ; công bố duplicates | Đã chạy thật. Train trùng nội bộ 1; không exact overlap giữa split. Near duplicates và điều khoản phân phối cần xem xét thêm |
| 3. Baseline | Hai pipeline, tuning logs, final metrics, CPU benchmark | Train/validation/test theo protocol, run complete, artifact reloadable | Hoàn thành thí nghiệm baseline. Test F1 sentiment 0.7015 và topic 0.7277: chưa đạt quality targets; không promote |
| 4. PhoBERT GPU | Hai completed task runs với pinned checkpoint và cùng data snapshot | Có checkpoint/tokenizer/config/metrics/predictions/Trainer state; nạp lại suy luận được | Đã import vào dự án, kiểm tra metrics và nạp CPU; 64/64 câu validation khớp GPU mỗi task. Test macro F1 = 0.8329/0.8075. Reload smoke check không phải chạy lại toàn dataset |
| 5. So sánh / lựa chọn | Comparison report, errors, CPU latency, dung lượng và quyết định | Cùng snapshot/phần cứng/scope; ít nhất 10 lỗi; chọn theo protocol | Hoàn tất đánh giá offline: chọn PhoBERT cho giai đoạn tích hợp API. CPU joint p95 372.70 ms so baseline 12.88 ms, 300 câu, một thread. Đã tích hợp và đo HTTP ở giai đoạn 6; không promote Joblib mới |
| 6. API và DB tích hợp | Model adapter thật, migrations, atomic writes, bounded imports/exports | Integration tests pass; DB/model path cô lập; model được chọn phục vụ đúng contract | Đã có adapter PhoBERT CPU, settings/lifespan/hash/version; 77 tests đạt. HTTP thật với SQLite tạm kiểm chứng single/batch/CSV và lỗi atomicity; 300 requests p95=359.60 ms. Chưa đo concurrency hoặc deploy public |
| 7. Frontend / reports | Single prediction, CSV, dashboard, filters, pagination/matrix, PDF charts | Luồng browser nhất quán, mobile/keyboard, export đúng dữ liệu | Đã thêm pagination/date/matrix, raw text, export errors và PDF charts. Build đạt; Edge/CDP desktop/mobile fixture checks đạt sau redesign. Chưa E2E PhoBERT/upload/export thật hoặc visual PDF; xem [UI review](reports/2026-11-07/ui-redesign.md) |
| 8. Nghiệm thu / bàn giao | Reproducible demo, báo cáo và slides | Test/build/E2E/load evidence, backup/restore, documentation đủ để người khác chạy | Chưa hoàn thành; phụ thuộc các gate trên |

## Quy tắc chuyển giai đoạn

- Phần có thể thực hiện độc lập như test, documentation và setup được làm song song; không đánh dấu nghiệm thu phụ thuộc model khi chưa có model evidence.
- Baseline chưa đạt ngưỡng không ngăn nghiên cứu PhoBERT theo preset đã chốt. Không sửa target hoặc dùng test để lặp tuning.
- Không promote model không đạt hoặc gọi toàn bộ đề tài hoàn thành trước comparison/UI/end-to-end evidence.
- Giai đoạn PhoBERT sử dụng Colab/Kaggle GPU theo lựa chọn của người dùng. Môi trường GPU ngoài phiên chat cần người dùng mở runtime và chạy notebook; không giả định đã có một phiên GPU được kết nối.

## Bước tiếp theo cụ thể

1. Đóng giai đoạn 7: chạy E2E UI với PhoBERT thật, CSV/upload/export, keyboard flow và review PDF trực quan. Các controls và thiết kế lại đã triển khai, không làm lại từ đầu.
2. Giai đoạn 8: kiểm thử tổng thể/demo và vận hành; bổ sung concurrency, backup/restore và release evidence khi đóng phạm vi bàn giao.
3. Tiếp tục đóng các gate nền tảng còn mở: gần trùng, điều khoản dataset, bảng truy vết yêu cầu và dependency lock. Không cần train lại chỉ để kiểm tra file.

Xem [audit trước đợt triển khai này](reports/2026-11-07/project-stage-audit-20261107.md) và [quyết định chọn model mới nhất](reports/2026-11-07/model-selection-20261107.md). Bảng này đã thống nhất đánh số 0–8 với kế hoạch gốc của người dùng.

Evidence được chia theo từng bước tại [danh mục reports](reports/README.md), không chỉ báo cáo baseline. Các checkbox trong tài liệu NLP là điều kiện cần xác minh, không tự động hoàn thành khi có code.

## Kết quả GPU đã nhận

Xem [kiểm tra hai ZIP PhoBERT](reports/2026-11-07/phobert-results-review-20261107.md), [reload/CPU benchmark và lựa chọn](reports/2026-11-07/model-selection-20261107.md), rồi [tích hợp HTTP/DB thật](reports/2026-11-07/api-integration-20261107.md). Bước tiếp theo là nghiệm thu UI với model thật và review export; không cần train lại vì lý do kiểm tra file.

## Đọc trạng thái đúng

- Backend default vẫn sklearn; launcher demo chọn PhoBERT qua config/demo.env. Không đồng nhất production.joblib legacy với checkpoint PhoBERT đang được cấu hình.
- CPU inference p95 và HTTP p95 đo khác scope/lần chạy; không trừ hai số để suy ra overhead.
- UI 100% confidence là softmax được làm tròn, không phải accuracy hay chắc chắn đúng 100%.
- Thiếu bằng chứng thì để mở gate; không đổi số liệu lịch sử để đồng bộ.

## Evidence chính

| Kết luận | Nguồn |
| --- | --- |
| Snapshot/counts/EDA và baseline | [Baseline report](reports/2026-11-07/execution-report-20261107.md), [manifest](../data/processed/uit-vsfc-v1/manifest.json) |
| Chất lượng PhoBERT, chọn model và CPU | [Model selection](reports/2026-11-07/model-selection-20261107.md), [comparison JSON](../artifacts/reviews/model-selection-20261107/comparison.json) |
| 77 tests và HTTP p95 359.60 ms | [API report](reports/2026-11-07/api-integration-20261107.md), [JUnit](../artifacts/reviews/api-integration-20261107/tests-phobert-env.xml), [HTTP report](../artifacts/reviews/api-integration-20261107/http-final.json) |
| UI build, desktop/mobile fixtures | [Redesign report](reports/2026-11-07/ui-redesign.md); screenshots/script là cache local, chưa có frontend E2E suite |
| Dotenv CLI test riêng | [Test source](../tests/test_cli_env.py); lần kiểm tra trước 1 passed, không phải full-suite run mới |

Model metrics đo trên UIT-VSFC và latency đo trên máy i5-1240P/RAM khoảng 8 GB. HTTP benchmark dùng một client tuần tự, batch=1 và SQLite tạm; không có bảo đảm concurrency/public production.
