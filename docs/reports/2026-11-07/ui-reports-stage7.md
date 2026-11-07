# Giai đoạn 7 — UI và báo cáo

> **Báo cáo theo thời điểm:** không dùng phần “bước tiếp theo/chưa có” trong báo cáo này làm trạng thái hiện hành. Xem [trạng thái hiện tại](../../status.md).

Cập nhật thiết kế: xem [Góc lắng nghe](ui-redesign.md). Đã kiểm chứng browser local bằng Edge/CDP với fixtures sau lần browser connector timeout bên dưới; chưa thay thế E2E PhoBERT/upload/export thật hoặc review PDF trực quan.

## Đã triển khai

- Dashboard phân trang 20 dòng, trang trước/sau, tổng số kết quả; thay bộ lọc trở về trang 1.
- Bộ lọc sentiment/topic và khoảng thời điểm dự đoán. Input dùng giờ máy người dùng, chuyển sang UTC ISO có timezone khi gửi API; cận trên không bao gồm. Khoảng ngược hiển thị lỗi.
- Bảng số liệu topic × sentiment và biểu đồ tổng hợp dùng cùng bộ lọc với bảng/export. Bảng phân trang; báo cáo xuất toàn bộ kết quả khớp bộ lọc, chịu giới hạn export backend.
- Hủy fetch cũ khi đổi bộ lọc/trang, tránh response cũ ghi đè; có loading/error/empty và retry. Xuất file qua fetch để hiển thị lỗi 413/503 thay vì mở trang lỗi mới.
- Analyze và Dashboard hiển thị raw_text; giữ khoảng trắng khi hiển thị, fallback text cho dữ liệu cũ. Confidence được mô tả là điểm tin cậy chưa bảo đảm calibration.
- PDF có hai biểu đồ phân bố, tính trực tiếp từ cùng tập rows đã lọc; giữ Unicode font, wrap/pagination, export limit và bảo vệ CSV hiện có. Chi tiết PDF dùng raw text khi có.

## Kiểm chứng thực tế

`npm.cmd --prefix frontend run build` bằng Node portable 24.22.2: đạt, Vite 5.4.19, 38 modules. `python -B -m pytest tests -q -p no:cacheprovider` trong .venv-phobert, BLAS/OMP threads=1: 77 passed, một Starlette/TestClient deprecation warning. Regression có PDF Unicode/wrapping/completeness và CSV/filter coverage, chưa thay thế kiểm chứng trực quan biểu đồ PDF.

Đã mở dev server Vite 127.0.0.1:5173; browser connector truy cập timeout. Chưa có browser flow, screenshots desktop/mobile hoặc kiểm chứng bàn phím trực tiếp. Không báo cáo build pass là UI acceptance.

## Điều kiện còn thiếu để đóng giai đoạn 7

1. Chạy UI với API PhoBERT theo [hướng dẫn](../../guides/phobert-api-guide.md) trên database demo riêng; nhập single/CSV rồi kiểm tra dashboard.
2. Tạo hơn 20 bản ghi, chuyển trang; đổi các bộ lọc và khoảng ngày, kiểm tra reset trang, số liệu bảng/matrix/biểu đồ và export cùng phạm vi.
3. Kiểm tra empty/error/retry, API mất kết nối, khoảng ngày sai và lỗi giới hạn export.
4. Kiểm tra desktop/mobile, thao tác bàn phím, tiêu đề/nhãn đọc được và ảnh chụp. Mở PDF xuất thật để kiểm tra font/biểu đồ/ngắt trang; kiểm tra CSV Unicode/formula safety.

Giai đoạn này đã có implementation và build/regression evidence, **chưa nghiệm thu đầy đủ** vì browser và visual PDF checks còn thiếu. Không sửa model, dataset, runtime database hoặc dependencies trong đợt UI này.
