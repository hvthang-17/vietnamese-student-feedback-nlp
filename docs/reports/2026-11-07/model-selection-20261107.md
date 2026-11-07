# Hoàn tất kiểm chứng checkpoint và chọn model tích hợp — 07/11/2026

> **Báo cáo theo thời điểm:** không dùng phần “bước tiếp theo/chưa có” trong báo cáo này làm trạng thái hiện hành. Xem [trạng thái hiện tại](../../status.md).

Cập nhật sau lần chọn model này: đã thêm adapter và kiểm chứng HTTP/DB thật; xem [báo cáo giai đoạn 6](api-integration-20261107.md). Các mục API còn thiếu bên dưới mô tả thời điểm lựa chọn offline.

## Quyết định và vị trí hiện tại

Chọn **PhoBERT để tích hợp API ở giai đoạn 6** theo [protocol](../../../tasks/experiment-protocol.md). Hai tác vụ đều có validation macro F1 cao hơn baseline; trung bình tăng 0.0904, lớn hơn khoảng hòa 0.01 đã chốt. PhoBERT đạt hai ngưỡng test F1 và benchmark CPU cho phép tiếp tục tích hợp trên máy hiện tại. Không lựa chọn chỉ vì mô hình phức tạp hơn.

Đã hoàn tất điều kiện nạp lại model của giai đoạn 4 và đánh giá offline/chọn ứng viên của giai đoạn 5. **Chưa nghiệm thu API hoặc deploy model mới.** Các thiếu sót nền tảng như kiểm tra gần trùng, điều khoản dataset và dependency lock tổng thể vẫn được giữ mở trong [audit](project-stage-audit-20261107.md); không coi toàn bộ giai đoạn trước là đã qua cổng đầy đủ.

## Những việc đã thực hiện

- Nhập hai ZIP người dùng cung cấp vào run riêng, giữ nguyên ZIP nguồn, không ghi đè run hay production. Kiểm tra CRC, đường dẫn, size limits, manifest/revision, label mapping và tái tính validation/test metrics từ predictions.
- Lưu checksum từng file trong [sentiment import receipt](../../../artifacts/runs/phobert-sentiment-20261106T185751304434Z/import.json) và [topic import receipt](../../../artifacts/runs/phobert-topic-20261106T191350538989Z/import.json). Không giải nén/nạp `training_args.bin`.
- Tạo môi trường `.venv-phobert` riêng cho CPU; giữ nguyên môi trường baseline. PyTorch 2.6.0+cpu, Transformers 4.57.1, PyVi 0.1.1; [package snapshot](../../../artifacts/reviews/model-selection-20261107/cpu-environment.txt). `pip check` đạt. Snapshot này ghi môi trường thực tế, chưa là lockfile đa nền tảng.
- Nạp model/tokenizer từ local files, chỉ dùng safetensors; `eval()` + `inference_mode()`, chuẩn hóa → PyVi → tokenizer giống training.
- So nhãn CPU với export GPU trên 64 câu validation đầu: **64/64 khớp cho sentiment và 64/64 khớp cho topic**. Đây là smoke/reload verification, không phải chạy lại toàn bộ validation/test. [Evidence](../../../artifacts/reviews/model-selection-20261107/reload-check.json).

Trọng số hiện nằm trong dự án:

```text
artifacts/runs/
├── phobert-sentiment-20261106T185751304434Z/best_model/model.safetensors
└── phobert-topic-20261106T191350538989Z/best_model/model.safetensors
```

`run.json` của GPU được giữ nguyên. `import.json` ghi trạng thái import; trường `inference_verified=false` tại thời điểm import không được sửa sau đó. Evidence reload được lưu riêng và xác định đúng file bằng hashes.

## So sánh chất lượng và chi phí

| Chỉ số | Baseline | PhoBERT |
| --- | ---: | ---: |
| Validation sentiment macro F1 | 0.7496 | 0.8752 |
| Validation topic macro F1 | 0.7530 | 0.8082 |
| Trung bình validation macro F1 | 0.7513 | 0.8417 |
| Test sentiment macro F1 | 0.7015 | 0.8329 |
| Test topic macro F1 | 0.7277 | 0.8075 |
| CPU mean, joint inference | 11.47 ms | 187.67 ms |
| CPU p95, joint inference | 12.88 ms | 372.70 ms |
| Dung lượng artifact/trọng số | 5,291,985 bytes | 1,080,055,996 bytes |

Máy đo: Intel Core i5-1240P, 16 logical CPUs, RAM 8,241,991,680 bytes, Windows, Python 3.11.9. Cả hai dùng CPU một thread, batch=1, 5 warmups, cùng 300 câu đầu test theo snapshot đã xác minh. Các run benchmark dùng trong bảng thực hiện tuần tự, không chạy test/train cùng lúc. Đây là một lần đo trên máy phát triển, không phải load test hoặc bảo đảm latency trên mọi máy.

Scope chung: chuẩn hóa và suy luận hai tác vụ; PhoBERT bao gồm PyVi, tokenization và softmax, baseline bao gồm vectorizer và hai predict_proba. Không gồm model load, HTTP, SQLite hoặc contention nhiều request. Phụ thuộc runtime khác nhau được ghi trong từng report. Cột dung lượng baseline gồm vectorizer+estimator; PhoBERT chỉ tính hai file weights, không gồm tokenizer/dependencies. Không diễn giải hai phạm vi dung lượng này như tổng footprint triển khai.

Nguồn: [baseline CPU tuần tự](../../../artifacts/reviews/model-selection-20261107/baseline-cpu-sequential.json), [PhoBERT CPU](../../../artifacts/reviews/model-selection-20261107/phobert-cpu.json), [bảng JSON đầy đủ](../../../artifacts/reviews/model-selection-20261107/comparison.json). JSON bao gồm accuracy, weighted F1, per-class metrics và confusion matrices; [review GPU](phobert-results-review-20261107.md) giải thích kiểm tra kết quả gốc. `baseline-cpu.json` trong cùng thư mục chỉ là diagnostic vì trùng thời gian chạy tests, không dùng trong bảng.

PhoBERT CPU benchmark ghi load/import 17.487 giây; reload check lần trước là 30.077 giây. Đây không phải cold-start benchmark kiểm soát disk cache. RSS sau inference khoảng 791 MB, peak working set ghi nhận khoảng 1.073 GB cho process đo; trọng số memory-mapped và bộ nhớ Windows có thể bị thu hồi nên không dùng RSS này làm mức RAM tối thiểu khi deploy nhiều worker. Không có phép đo RAM tương đương cho baseline.

## Bổ sung bảng chỉ số và căn cứ quyết định

Phần này tổng hợp lại evidence đã có, không phải thí nghiệm mới và không thay các số đo lịch sử. Metrics trong comparison.json đã được đối chiếu với metrics.json của baseline và từng task PhoBERT. Các chỉ số chất lượng dùng thang 0–1; chênh lệch ghi bằng **điểm phần trăm**, không phải phần trăm cải thiện tương đối.

### Điều kiện so sánh

- Cùng snapshot UIT-VSFC: train 11.426, validation 1.583, test 3.166; revision/hashes nằm trong [manifest](../../../data/processed/uit-vsfc-v1/manifest.json) và [comparison JSON](../../../artifacts/reviews/model-selection-20261107/comparison.json). Không dùng artifact synthetic legacy.
- Baseline là pipeline TF-IDF + SVM đã calibration; không lấy điểm tuning SVM chưa calibration thay cho pipeline cuối. PhoBERT là hai classifier riêng sentiment/topic.
- Cấu hình/chọn checkpoint dựa validation theo protocol; test dùng báo cáo cuối và đối chiếu mục tiêu. Không train/tune lại dựa trên test để tạo bảng này.
- Đây là một lần thí nghiệm cho mỗi hướng; chưa có multi-seed mean/std hoặc kiểm định ý nghĩa thống kê. Không khẳng định ưu thế trên mọi dữ liệu.

### Tổng hợp validation và test

| Split / tác vụ | Chỉ số | Baseline | PhoBERT | Chênh lệch (điểm %) |
| --- | --- | ---: | ---: | ---: |
| validation / sentiment | accuracy | 0.9141 | 0.9533 | +3.92 |
| validation / sentiment | macro_f1 | 0.7496 | 0.8752 | +12.56 |
| validation / sentiment | weighted_f1 | 0.9059 | 0.9518 | +4.59 |
| validation / topic | accuracy | 0.8806 | 0.8945 | +1.39 |
| validation / topic | macro_f1 | 0.7530 | 0.8082 | +5.52 |
| validation / topic | weighted_f1 | 0.8707 | 0.8939 | +2.32 |
| test / sentiment | accuracy | 0.8989 | 0.9403 | +4.14 |
| test / sentiment | macro_f1 | 0.7015 | 0.8329 | +13.14 |
| test / sentiment | weighted_f1 | 0.8856 | 0.9374 | +5.18 |
| test / topic | accuracy | 0.8642 | 0.8967 | +3.25 |
| test / topic | macro_f1 | 0.7277 | 0.8075 | +7.98 |
| test / topic | weighted_f1 | 0.8566 | 0.8953 | +3.87 |

Macro F1 xem các lớp ngang nhau, phù hợp khi neutral/others ít mẫu. Weighted F1 và accuracy chịu ảnh hưởng mạnh hơn từ lớp phổ biến; cần xem cả per-class và confusion matrix.

### Precision, recall và F1 từng lớp trên test

Support là số nhãn thật trong cùng tập test, giống nhau cho hai mô hình. P = precision, R = recall.

| Tác vụ / lớp | Support | Baseline P | Baseline R | Baseline F1 | PhoBERT P | PhoBERT R | PhoBERT F1 | ΔF1 (điểm %) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sentiment / negative | 1409 | 0.8724 | 0.9610 | 0.9146 | 0.9467 | 0.9702 | 0.9583 | +4.37 |
| sentiment / neutral | 167 | 0.7297 | 0.1617 | 0.2647 | 0.7094 | 0.4970 | 0.5845 | +31.98 |
| sentiment / positive | 1590 | 0.9290 | 0.9214 | 0.9252 | 0.9514 | 0.9604 | 0.9559 | +3.07 |
| topic / lecturer | 2290 | 0.9074 | 0.9415 | 0.9241 | 0.9397 | 0.9454 | 0.9425 | +1.84 |
| topic / training_program | 572 | 0.7015 | 0.7150 | 0.7082 | 0.7828 | 0.7937 | 0.7882 | +8.00 |
| topic / facility | 145 | 0.9281 | 0.8897 | 0.9085 | 0.9200 | 0.9517 | 0.9356 | +2.71 |
| topic / others | 159 | 0.6176 | 0.2642 | 0.3700 | 0.6212 | 0.5157 | 0.5636 | +19.36 |

Neutral và others vẫn là giới hạn đáng chú ý dù PhoBERT cải thiện: một số phản hồi mơ hồ/ngắn hoặc nhiều chủ đề có thể bị bỏ sót. Các bảng trên không phải confidence của một phản hồi mới.

### Confusion matrix trên test

Hàng là **nhãn thật**, cột là **nhãn dự đoán**. Thứ tự sentiment: negative, neutral, positive; topic: lecturer, training_program, facility, others. Các ô là số mẫu, không chuẩn hóa phần trăm.

#### baseline / sentiment

| Thật / dự đoán | negative | neutral | positive |
| --- | ---: | ---: | ---: |
| negative | 1354 | 4 | 51 |
| neutral | 79 | 27 | 61 |
| positive | 119 | 6 | 1465 |

#### phobert / sentiment

| Thật / dự đoán | negative | neutral | positive |
| --- | ---: | ---: | ---: |
| negative | 1367 | 18 | 24 |
| neutral | 30 | 83 | 54 |
| positive | 47 | 16 | 1527 |

#### baseline / topic

| Thật / dự đoán | lecturer | training_program | facility | others |
| --- | ---: | ---: | ---: | ---: |
| lecturer | 2156 | 115 | 5 | 14 |
| training_program | 149 | 409 | 3 | 11 |
| facility | 7 | 8 | 129 | 1 |
| others | 64 | 51 | 2 | 42 |

#### phobert / topic

| Thật / dự đoán | lecturer | training_program | facility | others |
| --- | ---: | ---: | ---: | ---: |
| lecturer | 2165 | 93 | 4 | 28 |
| training_program | 92 | 454 | 5 | 21 |
| facility | 3 | 3 | 138 | 1 |
| others | 44 | 30 | 3 | 82 |

Per-class và confusion matrices trên validation cũng có đầy đủ trong [comparison JSON](../../../artifacts/reviews/model-selection-20261107/comparison.json).

### Quyết định lựa chọn và mức nghiệm thu

| Tiêu chí | Baseline | PhoBERT | Nhận xét |
| --- | --- | --- | --- |
| Trung bình validation macro F1 | 0.7513 | 0.8417 | PhoBERT cao hơn 0.0904; vượt khoảng hòa 0.01 theo protocol |
| Test sentiment macro F1 ≥ 0.80 | Không đạt | Đạt | Không đổi ngưỡng để hợp thức hóa kết quả |
| Test topic macro F1 ≥ 0.75 | Không đạt | Đạt | Xét riêng từng tác vụ |
| CPU joint p95 | 12.88 ms | 372.70 ms | Baseline nhanh hơn; cùng 300 câu, batch=1, một thread; không phải HTTP |
| HTTP + SQLite p95 | Chưa đo cùng scope | 359.60 ms | PhoBERT có phép đo 300 request tuần tự, không suy ra overhead hoặc so HTTP hai model |
| Bộ nhớ/thời gian nạp | Chưa có phép đo tương đương | Có evidence trong phần chi phí phía trên | Không tự điền số hoặc kết luận RAM so sánh |

**Quyết định có evidence:** chọn PhoBERT làm mô hình cho luồng tích hợp/demo hiện tại. Lợi ích chất lượng rõ ở cả hai tác vụ theo validation, hai ngưỡng test đạt và HTTP tuần tự trên máy demo đã có evidence dưới 2 giây. Baseline giữ làm mốc nghiên cứu, có ưu thế tốc độ/dung lượng nhưng chưa đáp ứng mục tiêu chất lượng.

**Chưa phải quyết định phát hành production hoàn tất:** chưa đóng E2E UI với model thật/upload/export, visual PDF, tải đồng thời, backup/restore, dependency lock, near-duplicate analysis và điều khoản dataset. Production Joblib legacy không bị thay; demo chọn PhoBERT qua MODEL_BACKEND và hai imported run. Xem [status hiện hành](../../status.md) và [API integration](api-integration-20261107.md).

Các bước “chưa benchmark HTTP/DB” và “tiếp theo tích hợp model” ở phần lịch sử bên dưới mô tả thời điểm lựa chọn offline ban đầu; evidence bổ sung về HTTP nằm trong báo cáo giai đoạn 6. Không diễn giải chúng như trạng thái hiện tại.

## Phân tích 10 lỗi PhoBERT

Dùng validation để giải thích hạn chế, không tuning thêm từ các lỗi này. Index bắt đầu từ 0 trong `validation.jsonl`. Các diễn giải là giả thuyết cần xem ngữ cảnh/annotation, không kết luận nhãn chuẩn sai.

| Task / index | Nhãn thật → dự đoán | Nhận xét |
| --- | --- | --- |
| sentiment / 18 | neutral → negative | Câu phủ định việc có lời phê bình; tín hiệu phủ định và từ tiêu cực có thể gây nhầm. |
| sentiment / 28 | negative → positive | Đề nghị ôn tập/cập nhật nội dung thi, không diễn đạt cảm xúc trực tiếp. |
| sentiment / 30 | neutral → negative | Nhận xét việc tự tìm hiểu và hiểu vấn đề có hàm ý phê bình, ranh giới trung tính khó phân biệt. |
| sentiment / 51 | negative → positive | Câu rất ngắn về sự nghiêm khắc; cảm xúc phụ thuộc cách nhìn của người viết. |
| sentiment / 59 | positive → negative | Câu bổ sung thông tin về học hiệu quả, thiếu ngữ cảnh đánh giá trực tiếp. |
| topic / 9 | training_program → others | Nhận xét “một số vấn đề” chưa rõ, thiếu đối tượng được nhắc đến. |
| topic / 28 | lecturer → others | Đề nghị về ôn thi/giảng dạy nhưng không nêu rõ giảng viên. |
| topic / 56 | training_program → facility | Câu vừa nói máy phòng thực hành vừa nói học phí/tín chỉ; giao thoa hai chủ đề. |
| topic / 72 | training_program → lecturer | Việc thúc đẩy tự học có thể liên hệ chương trình hoặc hành động của giảng viên. |
| topic / 73 | training_program → others | Ẩn dụ về việc thử nghiệm môn học; chủ đề không được gọi tên trực tiếp. |

Các lớp yếu vẫn là neutral và others: test F1 lần lượt 0.5845 và 0.5636, recall 0.4970 và 0.5157. Không chỉ báo cáo điểm trung bình rồi bỏ qua hạn chế này. Không mở thêm vòng tuning dựa trên test đã xem.

## Kiểm chứng và giới hạn

- Regression cuối: **74 passed**, [JUnit](../../../artifacts/reviews/model-selection-20261107/tests-final.xml). Lệnh thực chạy: `python -B -m pytest tests -q -p no:cacheprovider --junitxml=artifacts/reviews/model-selection-20261107/tests-final.xml`, bằng Python trong `.venv`, BLAS/OMP threads=1. TestClient treo khi thử trong sandbox Windows; đã dừng lần đó và chạy đạt ngoài sandbox với database tạm.
- Đã chạy `import-phobert` cho cả hai ZIP; `verify-phobert --samples 64 --threads 1`; `benchmark-phobert --samples 300 --threads 1`; baseline `benchmark` tuần tự. Đường dẫn/run/output và lệnh đầy đủ ở [ML workflow](../../../ml/README.md); report lưu exact hashes của input. Help của ba CLI có regression coverage, không cần import Torch.
- Không train lại, không sửa snapshot, không thay nhãn, không tạo runtime DB và không promote. SHA-256 production vẫn là `bac9bfa510782a2f43f291a67280a23b07382f1f7e6dfa367fc83e1997a56917`.
- Chưa benchmark HTTP/DB, throughput/concurrency, dài 5.000 ký tự hoặc batch/import với PhoBERT; benchmark là 300 câu corpus. Chưa đo confidence calibration cho softmax. Không coi softmax confidence là xác suất chắc chắn đã hiệu chuẩn.
- Việc kiểm chứng không thay thế kiểm tra gần trùng/điều khoản dataset hoặc khóa toàn bộ dependencies. Những gate đó còn mở.

## Giai đoạn tiếp theo: tích hợp model thật

1. Thêm predictor adapter PhoBERT theo domain port; chọn backend rõ ràng qua settings, giữ label mapping và HTTP contracts.
2. Nạp model một lần trong lifespan, không I/O khi import; kiểm tra provenance/hashes và version. Giữ lựa chọn sklearn/demo có phạm vi rõ ràng, không giả lập PhoBERT bằng cách đổi đường dẫn Joblib.
3. Test tích hợp model thật trên database cô lập, single/batch/import và lỗi inference không lưu dở dang; giữ coverage fixtures để regression nhanh.
4. Đo API p95 gồm request + inference + DB trên máy demo; đánh giá giới hạn độ dài/batch. Chỉ khi có bằng chứng này mới xác nhận mục tiêu dưới 2 giây và quyết định release.

Giai đoạn 7–8 và các thiếu sót nền tảng vẫn chưa hoàn thành. Không triển khai tất cả bước này trong đợt kiểm chứng/chọn model hiện tại.
