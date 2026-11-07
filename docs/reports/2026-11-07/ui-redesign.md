# Thiết kế lại giao diện — Góc lắng nghe

## Điều chỉnh theo yêu cầu giữ biểu đồ và ma trận

Đã bỏ hai chế độ xem sau phản hồi người dùng: KPI, biểu đồ, ma trận và bảng trở lại hiển thị cùng trang. Chỉ bảng có vùng cuộn riêng, sticky column headers và pagination phía trên (10/20/50/100 dòng). Topbar/sidebar giữ nguyên. Build sau điều chỉnh đạt; các kiểm chứng chia chế độ ở mục lịch sử bên dưới không mô tả layout hiện hành.

## Cập nhật bố cục làm việc (trước điều chỉnh)

Sau bản redesign ban đầu, đã thêm topbar fixed, sidebar thu/mở (desktop icon rail/mobile drawer, đóng bằng Escape), Dashboard tách Danh sách và Biểu đồ & ma trận. Bộ lọc mặc định thu gọn; bảng có scroll riêng, sticky column headers, pagination phía trên và page size 10/20/50/100. Export giữ nguyên cùng filter scope.

Build sau cập nhật đạt (Vite 5.4.19, 39 modules). Edge/CDP fixture checks đạt cho sidebar collapse/expand, mobile open/close/Escape và focus restoration, chuyển view, page size reset/request, pagination, topbar fixed, desktop summary scroll độc lập và mobile không tràn ngang. Ảnh desktop/mobile đã xem trực tiếp; script/ảnh trong cache local `data/cache/ui-redesign/check-layout.cjs`, `layout-desktop.png`, `layout-mobile.png`. Đây là kiểm chứng UI giả, không phải lần chạy E2E PhoBERT mới; không chạy lại backend tests/train/benchmark.

> **Báo cáo theo thời điểm:** không dùng phần “bước tiếp theo/chưa có” trong báo cáo này làm trạng thái hiện hành. Xem [trạng thái hiện tại](../../status.md).

## Hướng thiết kế

Đối tượng là người tổng hợp phản hồi sinh viên bằng tiếng Việt. Ưu tiên đọc nội dung, hiểu hai nhãn độc lập và đi từ phản hồi đơn đến tổng quan dữ liệu. Không hiển thị số liệu/model accuracy trang trí hoặc giả làm kết quả thực tế.

Palette: nền #F3F2F8, trắng #FFFFFF, mực #30264F, tím #6551B4, xanh tích cực #276B58, đỏ tiêu cực #A44450. Typography: Be Vietnam Pro, fallback Segoe UI/sans-serif khi không tải được Google Fonts. Tiêu đề sentence case, căn trái, nội dung có giới hạn chiều dài dòng.

```text
Desktop
[ Điều hướng ] [ Trang hiện tại                       ]
[            ] [ Tiêu đề / mô tả                      ]
[            ] [ Nhập phản hồi      ][ Hướng dẫn      ]
[            ] [ Câu mẫu            ][ Hai tác vụ     ]
[            ] [ Kết quả / hướng dẫn bắt đầu          ]

Mobile
[ Tên ứng dụng                                       ]
[ Phân tích | Tổng quan | CSV                         ]
[ Nhập phản hồi                                      ]
[ Kết quả                                            ]
[ Hướng dẫn                                          ]
```

Sau review plan: bỏ hero số liệu và các thẻ đồng dạng; dùng hình tờ phản hồi ở phần hướng dẫn làm điểm nhận diện. Sidebar giữ nguyên trên desktop, chuyển thành nav ngang trên mobile. Không dùng chuyển động tự chạy. Giữ nội dung và con số thật trong dashboard; ma trận và bảng cuộn trong vùng riêng.

## Thay đổi

- Shell/brand/navigation mới, skip link, aria-current và viewport/lang metadata.
- Analyze: composer, câu mẫu có thể chọn, empty/loading/result, nhãn và confidence, thông tin model mở rộng. Khóa chỉnh input khi đang gửi; sửa input xóa kết quả cũ.
- CSV: vùng chọn file, mẫu cấu trúc và hướng dẫn chuẩn bị; đổi file/gửi lại xóa kết quả cũ. Không thêm khả năng drag/drop chưa triển khai.
- Dashboard: đồng bộ palette, bộ lọc, bảng, KPI và charts; giữ API, pagination, date filters và export đã có.
- Focus bàn phím, reduced-motion, breakpoints mobile/tablet, semantic labels không chỉ dựa vào màu; hiển thị nguyên nội dung gốc.

## Kiểm chứng

`npm.cmd --prefix frontend run build` với Node portable 24.22.2, Vite 5.4.19: đạt. Không thay dependencies hoặc backend/model/database.

Edge headless local qua CDP, viewport mobile 390×1000 và desktop 1440×1100: kiểm tra không tràn ngang toàn trang, empty validation, chọn câu mẫu, render kết quả fixture, dashboard/matrix, pagination trang 2, CSV thiếu file và lỗi dashboard. Tất cả đạt sau khi script chờ React render giữa thao tác. Các screenshot và script kiểm chứng nằm trong `data/cache/ui-redesign/`, là cache local không commit.

Ảnh desktop/mobile đã được xem trực tiếp để review bố cục. Sau review giảm cỡ tiêu đề mobile để tránh một từ rơi xuống dòng cuối và tăng chiều cao nút câu mẫu lên 44 px. Build cuối đạt sau các chỉnh này. Chưa chạy lại toàn luồng PhoBERT/upload/export thật với thiết kế mới; fixture browser chỉ xác minh UI, không phải evidence chất lượng mô hình hoặc E2E production. Việc kiểm tra PDF trực quan và các gate giai đoạn 7 khác trong [báo cáo UI](ui-reports-stage7.md) vẫn cần hoàn tất.
