# Chạy backend với PhoBERT CPU

Backend có hai lựa chọn rõ ràng: `MODEL_BACKEND=sklearn` (mặc định, tương thích cũ) và `MODEL_BACKEND=phobert`. PhoBERT dùng hai imported run, không đọc `MODEL_PATH` và không fallback sang keyword khi thiếu file/lỗi checksum.

Để chạy demo hằng ngày, dùng [launcher hai lệnh](demo.md). Các lệnh thủ công dưới đây dành cho setup và cấu hình nâng cao.

## Môi trường và cấu hình

Dùng Python 3.11 và môi trường `.venv-phobert` trong [ML workflow](../../ml/README.md), sau đó cài dependencies backend trong chính môi trường đó:

```powershell
.\.venv-phobert\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Chạy từ repository root. Đây là cấu hình demo local, không phải production public:

```powershell
$env:MODEL_BACKEND='phobert'
$env:PHOBERT_SENTIMENT_RUN='artifacts/runs/phobert-sentiment-20261106T185751304434Z'
$env:PHOBERT_TOPIC_RUN='artifacts/runs/phobert-topic-20261106T191350538989Z'
$env:PHOBERT_CPU_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:HF_HUB_OFFLINE='1'
$env:ALLOW_DEMO_MODEL='false'
$env:ENVIRONMENT='development'
$env:DATABASE_PATH='data/phobert-demo.db'
$env:AUTO_MIGRATE='true'
.\.venv-phobert\Scripts\python.exe -m backend.app serve
```

Lệnh serve tạo/migrate database demo được chỉ định khi chạy. Không trỏ vào database cần bảo vệ khi chưa kiểm tra đường dẫn/backup. Backend không tự load `.env`. Với production, giữ yêu cầu token, migrations áp dụng trước, CORS/HTTPS và provisioning riêng; không đưa shared token vào frontend.

`GET /health` phải trả `fallback_model=false` và model version bắt đầu bằng `phobert-`; `GET /ready` kiểm tra DB. Version gắn với hashes của hai imported run. Đổi run cần restart. Production Joblib cũ không bị sửa bởi việc chọn backend.

## Thiết kế adapter

- [Settings](../../backend/app/settings.py) chỉ đọc cấu hình/resolve paths, không mở model hoặc DB.
- [App factory](../../backend/app/main.py) chọn predictor trong lifespan qua [load_predictor](../../backend/app/inference.py).
- [PhoBERTService](../../backend/app/phobert.py) kiểm tra receipt và hashes, nguồn dataset, mapping, revision và sự nhất quán giữa hai task trước khi nạp. Receipt là kiểm tra integrity cục bộ, không phải chữ ký xác thực; chỉ dùng run tin cậy.
- [CPU runtime](../../backend/app/phobert_runtime.py) dùng chung với offline evaluation, không import ML training/dataset vào backend. Heavy dependencies chỉ import lúc khởi tạo. Chỉ đọc local safetensors, không deserialize `training_args.bin`.
- Giữ nguyên normalize → PyVi → tokenizer, max_length=128, softmax và mapping 3/4 lớp. Input dài vẫn được lưu đầy đủ nhưng model truncate token như lúc train; confidence softmax chưa được calibration.
- Một lock serialize model work/PyVi trong một process; kết nối DB và transaction chỉ bắt đầu sau inference. Nhiều worker sẽ nạp nhiều bản model và tăng RAM. Đây chưa phải giải pháp throughput/concurrency lớn.

## Kiểm chứng HTTP thật và benchmark

Chạy riêng khi không có train/test/build đồng thời:

```powershell
.\.venv-phobert\Scripts\python.exe -B -m ml.evaluation.api_benchmark --data-dir data/processed/uit-vsfc-v1 --sentiment-run artifacts/runs/phobert-sentiment-20261106T185751304434Z --topic-run artifacts/runs/phobert-topic-20261106T191350538989Z --samples 300 --output artifacts/reviews/api-integration-20261107/http.json
```

Output phải chưa tồn tại; chọn tên mới để đo lại. Script mở Uvicorn trên loopback/cổng tạm, tạo SQLite tạm rồi xóa sau khi đóng server. Đo từ client qua TCP: validation, joint inference và DB commit; một client tuần tự, không gồm startup. Có 5 warmups và kiểm chứng single/batch/CSV, 422, lỗi inference ở giữa batch không ghi một phần. Test lỗi là fault injection có chủ đích. Không dùng script này để kiểm thử server production hiện hữu.

Script là công cụ opt-in cho checkpoint thật; suite pytest mặc định dùng predictor fixtures để chạy nhanh. Regression của adapter có ở [test_phobert_serving.py](../../tests/test_phobert_serving.py). Chưa đo tải đồng thời, batch=100, CSV=1000 hoặc triển khai qua reverse proxy; không suy ra các trường hợp đó từ benchmark single request.
