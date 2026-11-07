# Kiểm tra tiến độ theo cổng nghiệm thu — 07/11/2026

> **Báo cáo theo thời điểm:** không dùng phần “bước tiếp theo/chưa có” trong báo cáo này làm trạng thái hiện hành. Xem [trạng thái hiện tại](../../status.md).

Đây là snapshot audit trước đợt kiểm chứng CPU. **Cập nhật sau audit:** đã import/nạp lại checkpoint, benchmark CPU và chọn PhoBERT cho tích hợp API; xem [báo cáo mới nhất](model-selection-20261107.md) và [bảng tiến độ hiện tại](../../../tasks/implementation-plan.md). Các thiếu sót dữ liệu/môi trường/UI/vận hành bên dưới vẫn mở nếu chưa được đóng trong báo cáo mới.

## Kết luận

Dự án ở cuối giai đoạn 4, chuẩn bị hoàn tất giai đoạn 5: đã có kết quả nghiên cứu baseline và hai tác vụ PhoBERT, nhưng chưa chọn model triển khai với đủ bằng chứng vận hành. Giai đoạn 4 còn thiếu kiểm chứng nạp lại checkpoint và suy luận. Không nên đánh dấu tất cả giai đoạn 0–4 là đã nghiệm thu đầy đủ.

Backend và frontend đã được làm song song; đây không phải lỗi về thứ tự nếu dùng predictor giả để phát triển. Tuy nhiên, code và test với fixtures không thay thế nghiệm thu tích hợp model thật. Chưa ở giai đoạn bàn giao sản phẩm.

Đánh số dưới đây theo kế hoạch 0–8 người dùng cung cấp: giai đoạn 0 là yêu cầu, giai đoạn 1 là thiết kế. Bảng implementation-plan trước đây ghép môi trường/protocol vào giai đoạn 0; cách đánh số khác nhau và chỉ dẫn train GPU đã lỗi thời gây nhầm lẫn.

## Đối chiếu từng giai đoạn

| Giai đoạn | Bằng chứng hiện có | Điều kiện còn thiếu / kết luận |
| --- | --- | --- |
| 0. Bài toán và yêu cầu | [PRD](../../../tasks/prd-vietnamese-student-feedback-nlp.md), [protocol](../../../tasks/experiment-protocol.md): hai classifier độc lập, nhãn, chức năng và ngưỡng F1/latency | Đã có nền tảng để thực nghiệm. Chưa có bảng nghiệm thu từng yêu cầu với evidence; không suy ra tất cả yêu cầu đã đạt từ việc có PRD. |
| 1. Thiết kế và tổ chức | [System design](../../architecture/system-design.md), [API](../../architecture/api-design.md), [DB](../../architecture/database-design.md), [app factory](../../../backend/app/main.py), [domain ports](../../../backend/app/domain/ports.py) | Kiến trúc cốt lõi đã triển khai và có regression evidence. Dependency lock, Git/CI và quy trình vận hành chưa hoàn chỉnh; phương án PhoBERT chưa có serving adapter. |
| 2. Dữ liệu và EDA | [Manifest](../../../data/processed/uit-vsfc-v1/manifest.json), [báo cáo chạy thật](execution-report-20261107.md): 11.426/1.583/3.166 mẫu, revision/checksums, phân bố nhãn, một bản ghi trùng trong train, không exact overlap giữa split | Đạt phần snapshot/EDA/preprocessing thực tế. Chưa kiểm tra gần trùng; điều kiện sử dụng/phân phối dataset chưa xác minh xong. Theo tiêu chí đầy đủ trong kế hoạch, chưa đóng giai đoạn này. |
| 3. Baseline | [Run](../../../artifacts/runs/baseline-uit-vsfc-v1/run.json), [metrics](../../../artifacts/runs/baseline-uit-vsfc-v1/metrics.json), [CPU benchmark](../../../artifacts/runs/baseline-uit-vsfc-v1/cpu.json), smoke test serialization trong [JUnit](../../../artifacts/runs/verification-20261107/tests.xml) | Thí nghiệm baseline đã hoàn thành. Test macro F1 0.7015/0.7277 chưa đạt mục tiêu; [eligibility](../../../artifacts/runs/baseline-uit-vsfc-v1/eligibility.json) từ chối promotion. Không cần ép baseline đạt ngưỡng mới được nghiên cứu PhoBERT. |
| 4. PhoBERT | [Review hai ZIP](phobert-results-review-20261107.md), [verification](../../../artifacts/reviews/phobert-20261107/verification.json): cùng snapshot, pinned revision, checkpoint selection, metrics tái tính khớp nhãn thật; test macro F1 0.8329/0.8075 | Đạt mục tiêu chất lượng của hai tác vụ. Chưa nạp lại checkpoint chạy inference local; kiểm tra header/CRC không đủ thay thế bước này. ZIP còn ngoài repository; chưa có best_model trong artifacts/runs. Giai đoạn gần hoàn thành, chưa nghiệm thu trọn vẹn. |
| 5. So sánh và lựa chọn | Đã có so sánh F1 validation/test và ít nhất 10 lỗi baseline trong [execution report](execution-report-20261107.md) | Đang thực hiện. Thiếu benchmark PhoBERT CPU cùng phạm vi/phần cứng, chi phí bộ nhớ/thời gian nạp và quyết định chọn model chính thức. Bổ sung phân tích lỗi PhoBERT để giải thích lựa chọn. |
| 6. Backend và DB | [Routers](../../../backend/app/api), [services](../../../backend/app/services), [repository](../../../backend/app/repository.py), [migrations](../../../backend/app/migrations.py); 65 tests có evidence pass | Phần mềm nền đã làm đáng kể. [Inference](../../../backend/app/inference.py) chỉ phục vụ sklearn; [promote](../../../ml/deployment/promote.py) chỉ nhận baseline. Chưa có integration evidence với PhoBERT hoặc model cuối, chưa nghiệm thu hệ thống model thật. |
| 7. UI và báo cáo | [Các pages](../../../frontend/src/pages), [build evidence](../../../artifacts/runs/verification-20261107/frontend-build.json) | Mới có UI cơ bản. [Dashboard](../../../frontend/src/pages/Dashboard.jsx) chưa có pagination/date filters/matrix controls; PDF chưa có biểu đồ theo yêu cầu. Chưa kiểm chứng browser, desktop/mobile và toàn luồng export. Build pass không phải nghiệm thu UI. |
| 8. Kiểm thử tổng thể và bàn giao | Có tài liệu setup, tests/build và báo cáo thí nghiệm | Chưa hoàn thành: thiếu E2E với model cuối, API p95 gồm inference + DB, backup/restore, kiểm chứng người khác chạy demo và bộ tài liệu/slides bàn giao. |

## Những bước đã đi trước và những gì chưa được phép kết luận

- Backend/UI được xây trước khi hoàn tất chọn model. Có thể giữ lại; không cần xóa hay làm lại từ đầu. Chỉ coi đây là nền phần mềm chờ nghiệm thu tích hợp.
- Có kết quả test của cả baseline và PhoBERT chưa chứng minh API đạt p95 dưới 2 giây. CPU baseline 17.44 ms p95 chỉ đo inference theo scope của benchmark, không đo HTTP hoặc DB.
- PhoBERT tốt hơn trên validation và test trong thí nghiệm này; chưa đủ kết luận phù hợp máy demo. Hai model có khoảng 1.08 GB trọng số tổng cộng, còn cần bộ nhớ runtime.
- Có production.joblib không chứng minh model nghiên cứu đã được triển khai. Không có bằng chứng promotion model mới; không được trình bày model hiện tại như PhoBERT.
- Có metrics tái tính khớp chứng minh tính nhất quán của kết quả đã xuất, chưa chứng minh đã chạy lại inference từ trọng số trên máy local.
- Các báo cáo synthetic/estimated lịch sử không được dùng thay bằng chứng UIT-VSFC thật. Không tuning tiếp trên test đã xem; cải tiến mới cần protocol đánh giá phù hợp.

## Thứ tự tiếp tục

1. Đóng các việc còn thiếu ở nền tảng: bảng truy vết yêu cầu–cách kiểm chứng, kiểm tra gần trùng và ghi rõ giới hạn điều khoản dataset; ghi môi trường thực tế và dependency mismatch.
2. Hoàn tất giai đoạn 4: đưa hai run vào vị trí artifacts riêng, giữ nguyên ZIP nguồn, kiểm chứng model/tokenizer nạp được và dự đoán đúng contract. Bước này chưa được thực hiện trong lần audit.
3. Hoàn tất giai đoạn 5: benchmark PhoBERT CPU cùng scope với baseline, bổ sung lỗi điển hình, viết quyết định chọn model và giới hạn chất lượng/chi phí. CLI benchmark hiện chỉ hỗ trợ baseline; phải bổ sung hỗ trợ trước khi có thể đo PhoBERT theo workflow.
4. Nghiệm thu giai đoạn 6 với model đã chọn: adapter nếu cần, integration tests và version/provenance rõ ràng. Không thay đường dẫn Joblib để giả lập phục vụ PhoBERT.
5. Hoàn tất giai đoạn 7 rồi mới nghiệm thu giai đoạn 8: UI thiếu chức năng, browser flows, API end-to-end performance, vận hành/demo và báo cáo.

Không cần train lại hai tác vụ hiện tại chỉ để kiểm tra file hoặc làm rõ tiến độ. Không khởi động thêm thí nghiệm khi chưa xác định nó giải quyết điều kiện nghiệm thu nào.

## Phạm vi kiểm tra lần này

Đối chiếu kế hoạch người dùng, source code, manifest, báo cáo thí nghiệm, review ZIP và evidence test/build đã lưu. Không chạy lại tests/build/train/inference; không deserialize model, di chuyển trọng số, sửa application code hay thay production. Evidence 65 tests/build là kết quả lần chạy trước, không phải lần chạy mới của audit này.
