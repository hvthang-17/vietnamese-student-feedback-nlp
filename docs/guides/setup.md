# Cài môi trường từ đầu

Chạy từ repository root; Python 3.11+ và Node.js 20+. Các lệnh dưới cài dependencies, không phải kết quả validation mới. Không chạy prepare/train lên thư mục snapshot/run đã tồn tại.

## Backend mặc định sklearn

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Development mặc định auto-migrate và có thể dùng artifact cũ hoặc keyword fallback. Kiểm tra DATABASE_PATH/backup trước khi chạy với dữ liệu quan trọng. Đây không phải cách chọn PhoBERT demo.

## PhoBERT CPU

```powershell
python -m venv .venv-phobert
.\.venv-phobert\Scripts\python.exe -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv-phobert\Scripts\python.exe -m pip install -r ml/requirements-phobert-cpu.txt
.\.venv-phobert\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Cần đủ hai trusted imported run trong config/demo.env. Nếu chưa có checkpoint, theo [ML workflow](../../ml/README.md); không giả định trọng số binary được phân phối cùng source. Không train lại chỉ để khởi động demo đã có trọng số.

## Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Có package-lock nên npm ci phù hợp cài mới. Demo launcher tự dùng Node portable trong cache nếu có, hoặc npm trên PATH; không tự tải/cài Node. Không dựa vào cache portable khi chuyển sang máy khác.

## Cấu hình và validation

Xem [demo](demo.md), [PhoBERT API](phobert-api-guide.md), [.env.example](../../.env.example), [config/demo.env](../../config/demo.env). Backend chỉ đọc dotenv khi được truyền --env-file, trước Settings; process environment ưu tiên. Vite đọc VITE_API_URL riêng. Không đưa token nội bộ vào VITE_*.

Từ root, trong môi trường tương ứng:

```powershell
python -B -m pytest tests -q -p no:cacheprovider
```

Từ frontend/: `npm run build`. Lint/typecheck/e2e suite và Python lockfile chưa được thiết lập. Xem status cho evidence đã chạy; source command tồn tại không có nghĩa đã chạy thành công trên mọi máy.
