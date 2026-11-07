# Model artifacts và lịch sử thí nghiệm

Pipeline mới ghi vào `runs/<name>/`; xem [ML workflow](../ml/README.md). Training không ghi đè production.joblib.

Các file baseline_metrics.json, baseline_tuning_log.json, model_comparison.json và production.joblib đang có là kết quả legacy. Baseline metrics ghi nguồn canonical_local_seed. Không dùng F1 của chúng làm kết quả UIT-VSFC thật. API vẫn nạp production.joblib cũ cho đến khi promote một run mới hợp lệ.

Không xóa các file này chỉ để bắt đầu lại. Chọn tên run mới; bước promote là thao tác riêng và cần --replace khi đã có model API.
