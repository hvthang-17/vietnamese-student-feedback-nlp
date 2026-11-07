# Demo local trên Windows

Mở hai PowerShell tại repository root:

```powershell
.\scripts\demo.ps1 backend
```

```powershell
.\scripts\demo.ps1 frontend
```

Mở http://localhost:5173 sau khi backend báo startup complete. Health: http://127.0.0.1:8000/health — fallback_model=false, model_version bắt đầu bằng phobert-. Dừng từng process bằng Ctrl+C.

Backend đọc [config/demo.env](../../config/demo.env) qua tùy chọn --env-file rõ ràng. Database demo là data/phobert-demo.db, giữ lại giữa các lần chạy; không thay production Joblib. Thay đường dẫn model/port trong file cấu hình nếu cần. Frontend launcher cố định backend 127.0.0.1:8000 và port 5173; nếu đổi port backend cần sửa URL trong launcher tương ứng.

Biến môi trường có sẵn trong terminal ưu tiên hơn file. Dùng PowerShell mới nếu trước đó đã thiết lập các biến cho môi trường khác. File này dành cho local demo không auth, không dùng để cấu hình public production. Credentials thật chỉ đặt ở file local bị ignore hoặc secret provisioning, không thêm vào config/demo.env.

Launcher dùng .venv-phobert và Node portable của dự án nếu có, hoặc Node/npm trên PATH. Không tự cài dependencies. Xem [setup PhoBERT](phobert-api-guide.md) nếu môi trường chưa có.

CLI backend cũng hỗ trợ `python -m backend.app serve --env-file PATH` và `migrate --env-file PATH`. Không tự load dotenv khi import modules; process environment có ưu tiên. Kiểm tra target DB và backup trước khi migrate.
