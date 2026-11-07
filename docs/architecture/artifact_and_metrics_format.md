# Artifact và metrics trong pipeline ML

Xem [workflow và lệnh](../../ml/README.md). Không dùng báo cáo legacy ở gốc artifacts làm đầu vào pipeline mới.

## Dataset snapshot

`data/processed/<name>/` chứa ba JSONL và manifest.json. Mỗi dòng có sentence đã chuẩn hóa, sentiment và topic. Manifest schema_version=1 ghi source=huggingface, dataset_name, resolved revision, preprocessing, sha256 và validation (counts, label distributions, duplicates, cross-split overlap).

## Baseline run

`artifacts/runs/<name>/` chứa run.json, model.joblib, metrics.json và predictions.json. Thư mục phải mới; status chỉ thành complete sau khi các output được ghi. Run metadata ghi môi trường/thư viện, config, manifest, model_version, artifact_sha256 và metrics_sha256.

Gói model.joblib là dictionary gồm model_version, model_type=sklearn_calibrated_pipeline, sentiment_model, topic_model, label_mappings, dataset, config và tuning_metadata. Hai model hỗ trợ predict_proba/classes_ theo API hiện tại. Không deserialize artifact không tin cậy.

Metrics chứa validation/test → sentiment/topic → accuracy, macro_f1, weighted_f1, per_class và confusion_matrix. Tất cả lớp trong mapping được tính vào macro F1, kể cả lớp vắng với F1=0. Các cờ acceptance_verification phản ánh ngưỡng số học; training chưa đo latency nên latency_target_met/all_criteria_met là false. Không suy diễn đây là lỗi quality khi chỉ thiếu bước benchmark.

## Benchmark và promote

CPU report ghi model_version, artifact_sha256, dataset_sha256/revision, scope, environment đo và benchmarks (mean/p50/p95/min/max/ms và measured_samples). Không ghi F1 mặc định. Promote đọc metrics và CPU report riêng, kiểm tra chúng khớp run, source và các ngưỡng. Chỉ sau promote, artifact được copy sang artifacts/production.joblib. Mặc định không thay model có sẵn.

## PhoBERT run

Mỗi task có run.json, metrics.json, predictions.json, best_model/ và checkpoints/. Metrics dùng cùng per-task schema với baseline, nhưng chỉ có task đang train; không giả lập tác vụ còn lại. Model checkpoint được pin bởi model_revision. Imported run có import.json ghi file hashes và nguồn ZIP; reload/CPU benchmark và API adapter đã có. Chọn hai run qua MODEL_BACKEND=phobert; CLI promote vẫn chỉ hỗ trợ baseline.

## Tính tái lập và giới hạn

Config snapshot là các setting code hiện dùng; môi trường package được ghi theo lần chạy. Chưa có Python lockfile. Checksum bảo vệ thay đổi file cục bộ, không phải chữ ký hoặc bằng chứng tự xác thực tính đúng của báo cáo. Cần review dữ liệu/thí nghiệm trước khi promote. Giữ nguyên báo cáo legacy, ghi rõ nguồn synthetic và không trộn với output mới.
