# Kết quả thực hiện bước dữ liệu và baseline — 07/11/2026

> **Báo cáo theo thời điểm:** không dùng phần “bước tiếp theo/chưa có” trong báo cáo này làm trạng thái hiện hành. Xem [trạng thái hiện tại](../../status.md).

Đây là kết quả chạy thật trên snapshot chính thức; không dùng artifact legacy canonical_local_seed. Protocol đã chốt tại [experiment-protocol](../../../tasks/experiment-protocol.md).

## 1. Dữ liệu đã kiểm định

Dataset revision: `2d76906157232f87e9883fa37ebfc91ffdee1f83`.

| Split | Số mẫu | Negative | Neutral | Positive | Trùng nội bộ |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 11426 | 5325 | 458 | 5643 | 1 |
| validation | 1583 | 705 | 73 | 805 | 0 |
| test | 3166 | 1409 | 167 | 1590 | 0 |

Không có exact normalized-text overlap giữa các split. Train có 1 bản ghi trùng nội bộ; giữ nguyên split chuẩn và công bố, không tự xóa. Near-duplicate detection chưa được thực hiện.

Source dataset card vẫn ghi license unknown: [UIT NLP dataset](https://huggingface.co/datasets/uitnlp/vietnamese_students_feedback). Kết quả hiện dùng cho đề tài học thuật; chưa xác minh quyền phát hành lại/thương mại hóa.

## 2. EDA đo từ snapshot

| Split | Ký tự min/max | Ký tự trung bình | Whitespace units trung bình |
| --- | --- | ---: | ---: |
| train | 4/660 | 59.08 | 14.31 |
| validation | 4/718 | 56.36 | 13.67 |
| test | 4/411 | 58.84 | 14.22 |

Whitespace units không phải số từ sau Vietnamese word segmentation. Mọi số đo ở đây là từ dữ liệu thật; các số trong EDA lịch sử không được tái sử dụng.

## 3. Baseline calibrated cuối cùng

| Split | Task | Accuracy | Macro F1 | Weighted F1 |
| --- | --- | ---: | ---: | ---: |
| validation | sentiment | 0.9141 | 0.7496 | 0.9059 |
| validation | topic | 0.8806 | 0.7530 | 0.8707 |
| test | sentiment | 0.8989 | 0.7015 | 0.8856 |
| test | topic | 0.8642 | 0.7277 | 0.8566 |

Run: [baseline-uit-vsfc-v1](../../../artifacts/runs/baseline-uit-vsfc-v1/run.json). Metrics đầy đủ gồm per-class và confusion matrices: [metrics.json](../../../artifacts/runs/baseline-uit-vsfc-v1/metrics.json).

Tuning uncalibrated chọn word+char n-gram cho cả hai tác vụ; sentiment C=0.5/balanced và topic C=1.0/balanced. Điểm tuning không đồng nghĩa điểm của calibrated pipeline cuối; bảng trên là pipeline cuối.

## 4. Acceptance hiện tại

- Sentiment test Macro F1 0.7015 < 0.80: CHƯA ĐẠT.
- Topic test Macro F1 0.7277 < 0.75: CHƯA ĐẠT.
- CPU joint inference mean 14.24 ms; p95 17.44 ms; 300 mẫu.
- Benchmark gồm normalize và hai predict_proba trên CPU, batch=1, không gồm load/HTTP/SQLite. Chưa đo API end-to-end.
- Không promote; không chỉnh ngưỡng hoặc lặp tuning theo test. Chưa chọn model thắng vì chưa có PhoBERT results.

## 5. Phân tích lỗi định lượng

- Neutral test: precision=0.7297, recall=0.1617, F1=0.2647.
- Others test: precision=0.6176, recall=0.2642, F1=0.37.
- Đây là điểm yếu ở các lớp ít mẫu; không suy ra nguyên nhân chỉ từ F1. Các ví dụ dưới phục vụ phân tích hậu nghiệm, không làm dữ liệu tuning mới.

| Test row (1-based) | Task | Nhãn thật | Dự đoán | Nội dung rút gọn |
| ---: | --- | --- | --- | --- |
| 28 | sentiment | neutral | positive | cách mà cô tiếp cận với sinh viên . |
| 36 | sentiment | neutral | positive | môn học này giúp chúng em hiểu ra những vấn đề cơ bản . |
| 54 | sentiment | neutral | negative | như vậy tụi em sẽ định hướng tốt hơn và tập trung vào những thứ cần thiết . |
| 122 | sentiment | neutral | positive | ví dụ phù hợp với nội dung kiến thức , hướng dẫn chi tiết . |
| 163 | sentiment | neutral | negative | giáo viên thực hành . |
| 13 | topic | others | facility | trong trường macbook thầy số hai thì không có máy nào số một . |
| 96 | topic | others | training_program | học thì quá ít nhưng khi thi thì quá nhiều yêu cầu viết code trong đề thi thì sao mà sinh viên  |
| 116 | topic | others | lecturer | sự nhiệt tình tận tâm . |
| 127 | topic | others | lecturer | đôi lúc sinh viên theo không kịp . |
| 170 | topic | others | training_program | các buổi ngoại khóa nên được mở . |

Các câu ngắn/thiếu ngữ cảnh và ranh giới nhãn cần được xem xét cùng annotation; không kết luận nhãn chuẩn sai chỉ vì model không đồng ý. Nghiên cứu cải tiến sau khi đọc test phải được công bố và đánh giá bằng protocol độc lập phù hợp.

## 6. Bước tiếp theo

Tại thời điểm chạy baseline, bước tiếp theo là train PhoBERT trên Colab/Kaggle. Sau đó đã nhận, kiểm tra ZIP, nạp lại CPU và benchmark; xem [quyết định chọn PhoBERT cho tích hợp API](model-selection-20261107.md). Không cần lặp bước train này. Các nhận xét chưa có PhoBERT ở phần baseline phía trên mô tả thời điểm chạy baseline, không phải trạng thái hiện tại.

## 7. Evidence môi trường

65 regression tests đã đạt; báo cáo [JUnit](../../../artifacts/runs/verification-20261107/tests.xml). Local dùng Python 3.11.9 và BLAS threads=1 cho các lệnh kiểm chứng/train. Global Node chưa được kích hoạt; đã tải Node 24.22.2 LTS portable vào cache dự án, kiểm tra SHA-256 và build frontend thành công (38 modules). Không thay Node toàn máy; browser E2E chưa chạy. Local huggingface-hub=2.2.0 khác constraint <1.0 trong requirements; môi trường thực tế được ghi lại, chưa coi là dependency lock tái lập.

Nguồn phiên bản GPU preset: [PyVi 0.1.1](https://pypi.org/project/pyvi/), [Transformers Trainer 4.57.1](https://huggingface.co/docs/transformers/v4.57.1/en/main_classes/trainer). Chưa cài hoặc train preset này trên GPU trong phiên hiện tại.
