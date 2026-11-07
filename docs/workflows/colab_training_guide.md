# Huấn luyện PhoBERT bằng Colab/Kaggle GPU

Hướng dẫn tái lập huấn luyện GPU, không phải trạng thái cần train lại. Đã có hai result ZIP được kiểm tra/import; xem [status](../status.md).

## File cần dùng

- [Notebook](../../notebooks/phobert_colab.ipynb): chỉ gọi CLI của dự án, không có bản training trùng lặp.
- [Code + official dataset snapshot ZIP](../../artifacts/handoff/phobert-colab-20261107.zip).
- [Bundle manifest](../../artifacts/handoff/phobert-colab-20261107.manifest.json).
- [Protocol đã chốt](../../tasks/experiment-protocol.md).

Dataset revision: `2d76906157232f87e9883fa37ebfc91ffdee1f83`.
Model: `vinai/phobert-base`, revision `01daacda68afe13d83023d16ec647239e344a1e6`.

## Colab

1. Mở Colab, upload notebook ở trên.
2. Chọn Runtime → Change runtime type → GPU. Nếu tài khoản chưa được cấp GPU, dừng ở preflight; không âm thầm train CPU.
3. Chạy cell upload và chọn đúng ZIP code-data, không chọn result ZIP.
4. Chạy install và GPU/PyVi preflight. Preset dùng Transformers 4.57.1, PyVi 0.1.1 và Torch >=2.6; môi trường GPU tách khỏi baseline Windows.
5. Cell lưu kết quả mặc định mount Google Drive do bạn cấp quyền trong runtime. Có thể tắt USE_GOOGLE_DRIVE, nhưng cần download trước khi runtime kết thúc.
6. Chạy sentiment rồi tải result ZIP ngay khi xong; tiếp tục topic và tải result ZIP thứ hai.

## Kaggle

Tạo notebook từ cùng file, bật Internet và accelerator GPU. Thêm ZIP code-data như input dataset; notebook tìm file đúng tên bên dưới /kaggle/input. Outputs ở /kaggle/working; dùng Save Version để giữ lại. Không cần mount Google Drive.

## File kết quả phải có

Mỗi ZIP chứa một completed run gồm run.json, metrics.json, predictions.json, best_model/tokenizer và trainer_state.json. Checkpoint training trung gian lớn được giữ trong nơi chạy nhưng không đưa hết vào result ZIP để tránh nhân bản trọng số. Không chỉ tải riêng một file weights.

Notebook kiểm tra checksum bundle và manifest; CLI tiếp tục kiểm tra revision, số mẫu và checksum snapshot. Train hai task trong process riêng, dùng seed/config thống nhất. Run name có timestamp và từ chối ghi đè.

Không điều chỉnh tham số vì nhìn thấy test thấp; kết quả baseline hiện chưa đạt ngưỡng vẫn được giữ nguyên. Khi có hai result ZIP, bước tiếp theo là đối chiếu metrics, CPU benchmark và chọn mô hình; PhoBERT được phục vụ qua adapter và imported task run paths; không dùng CLI promote baseline.

Hai run GPU có evidence; quota/thời lượng runtime của tài khoản cho lần chạy mới không được bảo đảm. Không có token, .env, production artifact hay database feedback riêng trong code bundle. Điều kiện phân phối dataset ngoài đề tài học thuật vẫn cần được xác minh.
