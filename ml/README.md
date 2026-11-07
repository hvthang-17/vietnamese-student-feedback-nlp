# ML workflow: thực hiện lại từ đầu

Đây là điểm bắt đầu chính cho phần nghiên cứu. Chạy mọi lệnh từ thư mục gốc bằng `python -m ml`; không chạy trực tiếp file bên trong package. Xem `python -m ml --help` hoặc thêm `--help` sau mỗi command. CLI help không cần import sklearn/torch.

## 1. Cấu trúc và trách nhiệm

```text
ml/
├── __main__.py              CLI duy nhất
├── core/
│   ├── config.py            Cấu hình thực dùng
│   └── runs.py              Run metadata, environment và ghi JSON
├── data/
│   ├── dataset.py           Download, validation, snapshot và checksum
│   └── eda.py               Thống kê đo từ snapshot thật
├── training/
│   ├── baseline.py          Tuning validation, calibrated SVM, test cuối
│   └── phobert.py           Fine-tune riêng từng task, early stopping
├── evaluation/
│   ├── metrics.py           Metrics chung, latency; không có điểm mặc định
│   └── benchmark.py         CPU benchmark cho baseline đã hoàn thành
└── deployment/
    └── promote.py           Kiểm tra điều kiện rồi thay model API
```

Các package có `__init__.py`; không chỉnh sys.path. Dataset snapshots đặt ngoài code trong `data/processed/`, experiments đặt trong `artifacts/runs/`.

## 2. Kiểm tra môi trường trước khi chạy

Dùng Python 3.11+ và cài requirements theo [README gốc](../README.md). Với PhoBERT, cài thêm `backend/requirements-transformers.txt` theo nhu cầu. Không cần Torch để dùng help hoặc chuẩn bị dữ liệu. Lệnh dưới giả định virtualenv đã được kích hoạt; nếu chưa, thay `python` bằng `.\.venv\Scripts\python.exe` trên Windows.

```powershell
python -m ml --help
python -B -m pytest tests/test_ml_workflow.py tests/test_data_integrity.py tests/test_preprocessing.py -q -p no:cacheprovider
```

Smoke test dùng dữ liệu nhỏ trong thư mục tạm để kiểm tra code; kết quả test không phải benchmark UIT-VSFC.

## 3. Prepare: tải và chốt dữ liệu

```powershell
python -m ml prepare --output data/processed/uit-vsfc-v1
```

Mặc định tải nhánh Parquet `refs/convert/parquet` của dataset chính thức. Loader resolve nhánh thành commit SHA trước khi tải. Có thể truyền `--revision COMMIT_SHA` của nhánh Parquet để tái lập chính xác. Không dùng commit của layout khác nếu nó không có các file `default/{split}/0000.parquet`.

Bước này tạo `train.jsonl`, `validation.jsonl`, `test.jsonl` và `manifest.json`: nguồn, commit, chuẩn hóa, SHA-256, số mẫu, phân bố nhãn và độ trùng. Kiểm tra đúng 11.426/1.583/3.166 mẫu, nhãn và nội dung rỗng. Không thay dữ liệu bằng synthetic khi lỗi mạng. Nếu lỗi: xử lý kết nối/đường dẫn rồi thử lại với thư mục mới; không dùng báo cáo cũ làm đầu vào.

Đọc `overlap_unique_texts` trong manifest. Các câu trùng được công bố, không tự xóa hoặc chia lại bộ chuẩn. Đây mới là kiểm tra exact match sau chuẩn hóa; near-duplicate detection chưa có. Hash phát hiện thay đổi file cục bộ, không phải chữ ký xác thực nguồn.

## 4. EDA: tạo báo cáo thật

```powershell
python -m ml eda --data-dir data/processed/uit-vsfc-v1 --output artifacts/runs/eda-v1.json
```

Xác minh checksum trước khi thống kê độ dài và ma trận topic × sentiment. Số đơn vị tách bằng whitespace không được gọi là số từ đã tách từ tiếng Việt. Phân bố và số đếm nằm trong dataset manifest kèm báo cáo. Không tạo thống kê giả khi không có dữ liệu.

EDA hiện mô tả cả ba split cho kiểm định dữ liệu; không dùng ví dụ/lỗi test để tuning. Muốn phân tích từ vựng để chọn đặc trưng, chỉ làm trên train.

## 5. Train baseline: run riêng

```powershell
python -m ml train-baseline --data-dir data/processed/uit-vsfc-v1 --run-dir artifacts/runs/baseline-v1
```

Thư mục run phải chưa tồn tại. Tuning n-gram/C/class_weight chỉ dùng validation; fit classifier và vectorizer trong từng fold calibration. Đánh giá pipeline cuối trên validation/test, lưu model và metrics. Training không đo latency và không thay `production.joblib`.

```text
artifacts/runs/baseline-v1/
├── run.json                 config, dataset, versions, status và hashes
├── model.joblib             Gói sklearn tương thích API
├── metrics.json             Validation/test từng task, chưa đo latency
└── predictions.json         Nhãn dự đoán theo thứ tự trong snapshot
```

`status=running` sau khi lỗi nghĩa là run chưa hoàn thành; không dùng nó để benchmark/promote. Giữ run đó để chẩn đoán và chọn tên run mới. Các lần lặp tuning không được dựa vào test; nếu đã dùng test để cải tiến, công bố và cần đánh giá độc lập mới.

## 6. PhoBERT: nhánh tùy chọn sau baseline

```powershell
python -m ml train-phobert --data-dir data/processed/uit-vsfc-v1 --run-dir artifacts/runs/phobert-sentiment-v1 --task sentiment --model-revision MODEL_COMMIT_SHA
python -m ml train-phobert --data-dir data/processed/uit-vsfc-v1 --run-dir artifacts/runs/phobert-topic-v1 --task topic --model-revision MODEL_COMMIT_SHA
```

Thay `MODEL_COMMIT_SHA` bằng commit 40 ký tự của `vinai/phobert-base`. Dùng cùng snapshot như baseline, chuẩn hóa → PyVi → tokenizer. Cấu hình trong `core/config.py`, bao gồm warmup_ratio, macro_f1 và early-stopping patience. Gọi set_seed trước khởi tạo model.

Mỗi task lưu `run.json`, `metrics.json`, `predictions.json`, `checkpoints/` và `best_model/`. Metrics từng lớp dùng cùng hàm với baseline. Sau khi nhận ZIP, dùng các stage kiểm chứng/benchmark CPU dưới đây. Adapter API PhoBERT có hướng dẫn tại [PhoBERT API](../docs/guides/phobert-api-guide.md); không dùng `promote` baseline cho checkpoint PhoBERT.

### Nhận kết quả GPU và kiểm chứng CPU

Với hai ZIP do chính bạn huấn luyện, nhập từng task bằng CLI. Lệnh từ chối ghi đè, kiểm tra manifest/metrics với snapshot local, CRC và đường dẫn ZIP; lưu SHA-256 từng file vào `import.json`. Không nạp hoặc giải nén `training_args.bin`. Đây là import để đánh giá, không phải promotion API.

```powershell
python -m ml import-phobert --archive PATH_TO_SENTIMENT_RESULTS.zip --data-dir data/processed/uit-vsfc-v1
python -m ml import-phobert --archive PATH_TO_TOPIC_RESULTS.zip --data-dir data/processed/uit-vsfc-v1
```

`PATH_TO_*` là placeholder, cần thay bằng ZIP thật. Thư mục đích mặc định `artifacts/runs/<tên run trong ZIP>`. Giữ nguyên `run.json` của GPU; `import.json` lưu nguồn và hashes, report verify lưu riêng để không sửa provenance cũ.

Trên Windows/Python 3.11, tạo môi trường CPU riêng, không dùng lại môi trường baseline:

```powershell
python -m venv .venv-phobert
.\.venv-phobert\Scripts\python.exe -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv-phobert\Scripts\python.exe -m pip install -r ml/requirements-phobert-cpu.txt
```

Hai lệnh bên dưới dùng các run thực tế đã nhận; chọn tên output mới nếu file đã tồn tại. Export `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `HF_HUB_OFFLINE=1` và `PYTHONIOENCODING=utf-8` cho process chạy. Model/tokenizer chỉ đọc local files, chỉ dùng safetensors và `eval()`/`inference_mode()`; chuẩn hóa → PyVi → tokenizer max_length=128 giống training.

```powershell
.\.venv-phobert\Scripts\python.exe -B -m ml verify-phobert --data-dir data/processed/uit-vsfc-v1 --sentiment-run artifacts/runs/phobert-sentiment-20261106T185751304434Z --topic-run artifacts/runs/phobert-topic-20261106T191350538989Z --samples 64 --threads 1 --output artifacts/reviews/reload-check.json
.\.venv-phobert\Scripts\python.exe -B -m ml benchmark-phobert --data-dir data/processed/uit-vsfc-v1 --sentiment-run artifacts/runs/phobert-sentiment-20261106T185751304434Z --topic-run artifacts/runs/phobert-topic-20261106T191350538989Z --samples 300 --threads 1 --output artifacts/reviews/phobert-cpu.json
```

Verify so nhãn CPU với predictions GPU theo thứ tự validation; mặc định chỉ 64 câu, không được gọi là đánh giá lại toàn validation/test. Muốn đối chiếu toàn validation truyền `--samples 1583`. Report mismatch được lưu và CLI trả lỗi nếu có khác biệt. Benchmark đo joint sentiment+topic batch=1 sau 5 warmups, cùng 300 câu đầu test như baseline. Ghi thời gian nạp riêng, RAM process, environment, threads và hashes. Không chạy tests/build/training cùng benchmark; số liệu này chưa bao gồm HTTP/DB. Adapter API hiện dùng cấu hình task run riêng; xem [hướng dẫn API](../docs/guides/phobert-api-guide.md). CLI promote vẫn chỉ dành cho baseline.

## 7. Benchmark baseline

```powershell
python -m ml benchmark --data-dir data/processed/uit-vsfc-v1 --run-dir artifacts/runs/baseline-v1 --output artifacts/runs/baseline-v1/cpu.json
```

Chỉ nạp run hoàn thành từ nguồn tin cậy, kiểm tra artifact hash và snapshot trùng với training. Đo tối đa 300 câu test sau warmup, batch=1, gồm normalize và predict_proba của cả hai classifier. Không gồm model load, HTTP và SQLite. Ghi environment đo thực tế, mean/p50/p95 và số mẫu; không chèn F1 giả vào benchmark.

## 8. Promote riêng sau khi review

```powershell
python -m ml promote --run-dir artifacts/runs/baseline-v1 --benchmark artifacts/runs/baseline-v1/cpu.json
```

Kiểm tra run hoàn thành, nguồn dữ liệu, artifact/metrics hashes, model version, dataset benchmark và các ngưỡng test F1/latency. Chỉ hỗ trợ baseline. Nếu API đã có model, lệnh từ chối; dùng `--replace` sau khi chủ động chọn thay model. Khởi động lại API sau promote. Đây là acceptance gate cho một run, chưa phải công cụ tự chọn mô hình thắng giữa nhiều run hoặc hệ thống rollback.

## 9. Bắt đầu lại mà không mất kết quả

Chọn tên snapshot/run mới (`v2`, `v3`...), không cần xóa database hoặc artifact hiện có. Mọi output mới mặc định từ chối ghi đè. Nếu muốn chạy cùng dữ liệu, giữ snapshot đã xác minh và chỉ tạo run mới.

Các file cũ `artifacts/baseline_metrics.json`, `baseline_tuning_log.json`, `model_comparison.json`, `production.joblib` và `docs/eda_*` được giữ nguyên vì là kết quả lịch sử. Baseline cũ ghi nguồn `canonical_local_seed`; không dùng để nghiệm thu, benchmark mới hoặc promote. API hiện vẫn có thể nạp model cũ cho đến khi bạn promote model mới hợp lệ.

## Những code đã bỏ

- Loader sinh mẫu tự động khi tải UIT-VSFC thất bại.
- EDA từ số liệu ước lượng hoặc câu mẫu.
- Benchmark tự điền F1 khi không có phép đo.
- Script train ghi thẳng production và notebook lặp lại pipeline với lệnh cleanup.

Các đường dẫn `python ml/train_*.py`, `ml/eda.py` và `ml/benchmark_cpu.py` cũ đã bị thay bằng CLI trên; không có wrapper legacy để tránh hai luồng thực thi.
