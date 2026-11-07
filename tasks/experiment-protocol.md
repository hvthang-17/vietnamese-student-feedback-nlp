# Experiment protocol — UIT-VSFC v1

Ngày chốt: 07/11/2026, trước baseline run chính thức đầu tiên. Phạm vi học thuật; PhoBERT train trên Colab/Kaggle GPU theo lựa chọn của người dùng. Không thay production artifact trong lúc thực nghiệm.

## Dataset và preprocessing

- Snapshot: data/processed/uit-vsfc-v1; manifest ghi immutable revision, hashes và số mẫu thực.
- Giữ split chuẩn 11.426/1.583/3.166. Không resplit hoặc deduplicate âm thầm.
- Chuẩn hóa NFC và whitespace; giữ dấu, punctuation, negation; không thêm từ điển viết tắt theo test.
- Seed mặc định 42. EDA kiểm định các split; quyết định đặc trưng chỉ dùng train/validation.

## Baseline đã chốt trước khi chạy

- Hai classifier riêng: sentiment/topic.
- Word TF-IDF (1,2), min_df=2, max_df=0.95, sublinear_tf=true.
- So sánh thêm char TF-IDF (3,5), min_df=5; chỉ thêm khi validation macro F1 tăng >0.002 ở cấu hình ablation.
- Grid C = 0.5/1/2, class_weight = balanced/None; chọn theo validation macro F1.
- CalibratedClassifierCV cv=3, sigmoid; TF-IDF/classifier được fit trong từng train fold.
- Đánh giá pipeline calibrated cuối trên validation/test. CLI train hiện tự đánh giá test ở cuối: không chạy nhiều lần rồi chọn run bằng điểm test.

## PhoBERT preset

- vinai/phobert-base, checkpoint commit được pin trước khi train; PyVi + tokenizer cùng checkpoint.
- max_length=128, train/eval batch=8/16, LR=2e-5, epochs tối đa=5, weight_decay=0.01, warmup_ratio=0.1.
- Chọn checkpoint bằng validation macro F1, early-stopping patience=2; seed=42 trước model init.
- Hai run/task độc lập dùng cùng snapshot và code bundle với baseline. Không tuning theo test.

## Model selection và acceptance

- Model selection dựa validation macro F1 của cả hai tác vụ và tài nguyên. Tổng hợp để so sánh: trung bình hai validation macro F1; nếu chênh không quá 0.01, ưu tiên latency thấp và đơn giản vận hành. Không bỏ qua tác vụ yếu chỉ vì điểm trung bình cao.
- Test dùng để báo cáo cuối và đối chiếu mục tiêu đã chốt: sentiment >=0.80, topic >=0.75. Nếu không đạt, báo cáo trung thực; không thay ngưỡng sau khi xem test chỉ để promote.
- So sánh cả accuracy/weighted F1/per-class metrics/confusion matrix, artifact size và CPU latency cùng phạm vi. Phân tích ít nhất 10 lỗi nếu có.
- CPU inference benchmark và HTTP end-to-end là hai số đo riêng. API p95 mục tiêu <2s trên máy demo được công bố, không tự coi inference p95 là HTTP p95.
- Chưa chọn model cuối hoặc promote trước khi có bằng chứng của hai hướng, trừ khi người dùng chủ động điều chỉnh phạm vi.

## Evidence

Lưu manifest, run.json, config, environment, metrics, predictions và benchmark không ghi đè. Kết quả legacy canonical_local_seed không được trộn với kết quả chính thức. Mọi thay đổi protocol sau đây phải có ngày, lý do và đánh giá ảnh hưởng đến tính độc lập của test.
