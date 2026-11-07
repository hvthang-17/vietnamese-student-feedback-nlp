# Giai đoạn 6 — tích hợp PhoBERT với API và SQLite

> **Báo cáo theo thời điểm:** không dùng phần “bước tiếp theo/chưa có” trong báo cáo này làm trạng thái hiện hành. Xem [trạng thái hiện tại](../../status.md).

## Phạm vi hoàn thành

Đã thêm predictor adapter PhoBERT CPU, chọn backend qua settings, nạp hai model trong lifespan và giữ nguyên HTTP contracts, labels, raw/normalized text, timestamps và giao dịch DB. Default vẫn là sklearn; không sửa production.joblib hoặc database feedback thật. Chọn PhoBERT rõ ràng qua cấu hình trong [hướng dẫn chạy](../../guides/phobert-api-guide.md).

Backend không phụ thuộc ML training hoặc snapshot khi serving. [Runtime](../../../backend/app/phobert_runtime.py) được dùng chung cho adapter và offline evaluation, giữ đúng preprocessing/tokenization/max_length=128 và eval/inference mode. [Adapter](../../../backend/app/phobert.py) xác minh file hashes, dataset provenance, revision và mapping; lỗi startup không fallback sang keyword. Model version gắn với hashes hai run. Receipt không phải chữ ký; chỉ dùng checkpoint tin cậy.

Một lock giới hạn model work/PyVi trong một process. SQL writer transaction vẫn mở sau inference. Nhiều worker sẽ tăng RAM và không được coi là đã kiểm chứng trong lần này.

## Kiểm chứng

- Regression môi trường baseline trước sửa logging: 76 passed, [JUnit](../../../artifacts/reviews/api-integration-20261107/tests.xml).
- Regression cuối trên chính `.venv-phobert`: **77 passed**, [JUnit](../../../artifacts/reviews/api-integration-20261107/tests-phobert-env.xml). Có một deprecation warning từ Starlette/TestClient về httpx; không tự cài thêm/đổi test framework vì cảnh báo này.
- Lệnh cuối: `.\.venv-phobert\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider --junitxml=artifacts/reviews/api-integration-20261107/tests-phobert-env.xml`, BLAS/OMP threads=1, chạy ngoài sandbox Windows do giới hạn TestClient trước đó.
- [Environment snapshot](../../../artifacts/reviews/api-integration-20261107/environment.txt); `pip check` đạt. Dependencies backend được cài trong virtualenv PhoBERT riêng, không thay `.venv` baseline. Đây là snapshot thực tế, chưa thay thế dependency lock.

[Công cụ HTTP opt-in](../../../ml/evaluation/api_benchmark.py) chạy Uvicorn thật trên TCP loopback/cổng tạm với checkpoint thật, dùng SQLite tạm và xóa sau shutdown. Đã kiểm chứng health/readiness, single prediction và dữ liệu đã lưu, batch giữ thứ tự, CSV nhận hai dòng hợp lệ/báo một dòng không hợp lệ, input rỗng trả 422. Fault injection làm lần suy luận thứ hai của batch lỗi: API trả 500 redacted, tổng số bản ghi không tăng.

Fault injection ở lần chạy đầu phát hiện traceback vẫn thoát ra Uvicorn dù response đã redacted. Đã sửa request middleware để trả lỗi sanitized và chỉ log request ID/error type; có regression dùng TestClient với raise_server_exceptions=True. Lần HTTP cuối chạy sau sửa này. Lỗi RuntimeError được log ở bước fault injection là chủ đích kiểm thử, không phải lỗi model tự phát.

## Giới hạn nghiệm thu

Lần đo cuối: **HTTP p95 = 359.60 ms**, mean=186.54 ms, max=788.47 ms trên 300 requests, đạt mục tiêu dưới 2 giây trong phạm vi đo này. Probe 5.000 ký tự=689.27 ms. Xem [report cuối](../../../artifacts/reviews/api-integration-20261107/http-final.json). [Report đầu](../../../artifacts/reviews/api-integration-20261107/http.json) được giữ làm lịch sử trước bản sửa logging, không dùng làm kết quả cuối.

Benchmark HTTP gồm TCP client request, validation, normalize/PyVi/tokenizer, hai model và SQLite commit; không phải TestClient timing. Dùng máy i5-1240P/16 logical CPUs/RAM khoảng 8 GB, một CPU thread, một client tuần tự, 5 warmups, 300 câu đầu test cùng snapshot đã xác minh. Không gồm startup, TLS, proxy, mạng ngoài máy hoặc tải đồng thời. Không chạy tests/train cùng benchmark.

Một probe input 5.000 ký tự kiểm tra API chấp nhận/lưu input dài; model vẫn truncate ở 128 token giống training. Probe đơn lẻ không phải p95 cho mọi văn bản dài. Chưa kiểm chứng batch=100, CSV=1000, throughput/concurrency, multi-worker hoặc public production deployment. Confidence softmax chưa calibration. Không coi kết quả đo này là SLA tổng quát.

SHA-256 production Joblib vẫn là `bac9bfa510782a2f43f291a67280a23b07382f1f7e6dfa367fc83e1997a56917`; không có `data/feedback.db` được tạo bởi lần kiểm chứng. Snapshot dữ liệu và trọng số không đổi.

## Tiếp theo

Giai đoạn 7: hoàn thiện UI pagination/date filters/matrix, hiển thị raw text phù hợp, đồng bộ dữ liệu bảng/biểu đồ/export, kiểm chứng desktop/mobile/browser. Giai đoạn 8 và các gate nền tảng (gần trùng, điều khoản dữ liệu, lockfile, backup/restore) còn mở. Không tự coi UI hoặc triển khai public đã đạt chỉ vì API benchmark đạt.
