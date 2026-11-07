# Kiểm tra hai kết quả PhoBERT — 07/11/2026

> **Báo cáo theo thời điểm:** không dùng phần “bước tiếp theo/chưa có” trong báo cáo này làm trạng thái hiện hành. Xem [trạng thái hiện tại](../../status.md).

Bản này ghi lần kiểm tra ZIP ban đầu. Sau đó đã import hai checkpoint vào dự án, kiểm chứng CPU và benchmark; xem [kết quả tiếp theo](model-selection-20261107.md). Các câu “chưa nạp lại/chưa benchmark” bên dưới mô tả phạm vi lần review ZIP, không phải tiến độ mới nhất.

Hai ZIP do người dùng cung cấp đã được đọc trực tiếp, không giải nén hoặc deserialize trọng số/pickle. CRC kiểm tra toàn ZIP đều hợp lệ. Không thay model API.

## So sánh chất lượng đã kiểm chứng

| Task | Baseline test Macro F1 | PhoBERT validation Macro F1 | PhoBERT test Macro F1 | Cải thiện (điểm %) | Test accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| sentiment | 0.7015 | 0.8752 | 0.8329 | +13.14 | 0.9403 |
| topic | 0.7277 | 0.8082 | 0.8075 | +7.98 | 0.8967 |

## Integrity và protocol

- Hai run complete, task đúng, device metadata cuda:0. Dataset manifest/revision/checksum khớp snapshot local và baseline.
- Đã tái tính toàn bộ metrics từ predictions.json với nhãn snapshot local: accuracy, macro/weighted F1, từng lớp và confusion matrix khớp hoàn toàn cho 1.583 validation và 3.166 test ở mỗi task.
- Model revision, config, seed và preprocessing khớp giữa hai run. Label mapping và classifier head shapes phù hợp 3/4 lớp.
- Đọc safetensors header: tensor shapes, byte ranges liên tục và kích thước phù hợp. Đây là kiểm tra cấu trúc, không phải xác nhận chạy lại inference.

## Checkpoint selection

- sentiment: best epoch=3.0, checkpoint=checkpoint-4287, cuối run epoch=5.0, global_step=7145. Best validation metric khớp metrics.json.
- topic: best epoch=5.0, checkpoint=checkpoint-7145, cuối run epoch=5.0, global_step=7145. Best validation metric khớp metrics.json.

## Các lớp cần chú ý

| Task / lớp | Baseline test F1 | PhoBERT test F1 | PhoBERT recall |
| --- | ---: | ---: | ---: |
| sentiment / neutral | 0.2647 | 0.5845 | 0.4970 |
| topic / others | 0.3700 | 0.5636 | 0.5157 |

## Kết luận có giới hạn

PhoBERT đạt ngưỡng chất lượng đã đặt (sentiment >=0.80, topic >=0.75) và tốt hơn baseline trong lần thí nghiệm này. Validation cũng cao hơn cho cả hai tác vụ, phù hợp protocol chọn theo validation. Chưa kết luận đạt nghiệm thu vận hành: thiếu benchmark CPU, latency API toàn request, model adapter và integration tests bằng checkpoint thật.

Mỗi model khoảng 540 MB trọng số; hai model cần thêm RAM cho runtime/activations, không chỉ dung lượng file. Hai run đã chạy GPU theo metadata; bản ZIP không ghi tên GPU cụ thể. Chưa đo confidence calibration cho softmax.

Không load training_args.bin vì đây là pickle; không có optimizer/RNG checkpoint đầy đủ để hứa resume training. Best_model/tokenizer và Trainer state cần cho đánh giá/inference đã có.

[Báo cáo JSON chi tiết](../../../artifacts/reviews/phobert-20261107/verification.json). Bước tiếp theo: benchmark CPU rồi tích hợp predictor adapter nếu phù hợp; không retrain chỉ để tăng điểm trên test đã xem.
