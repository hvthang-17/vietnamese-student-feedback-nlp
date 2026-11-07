# 06. Hệ thống, kiến thức liên quan và dàn ý trình bày

[Chỉ mục](README.md)

## Từ mô hình đến ứng dụng

```text
React: nhập phản hồi / CSV
            ↓ HTTP
FastAPI router: kiểm tra dữ liệu và định tuyến
            ↓
Feedback service → InferenceService → hai mô hình
            ↓
SQLite: phản hồi + kết quả + model_version + predicted_at
            ↓
Repository → thống kê / danh sách / xuất báo cáo
```

Router thuộc backend/app/api, điều phối ở services/feedback.py; truy vấn đọc/ghi nằm trong SQLite repository adapter, kết nối do app factory inject. Xem [kiến trúc chi tiết](../architecture/README.md).

HTTP/JSON giúp giao diện và dịch vụ tách rời. Pydantic kiểm tra schema, không kiểm chứng nghĩa câu hay nhãn thật. CORS quy định trình duyệt từ origin nào được truy cập, không phải cơ chế xác thực người dùng. SQLite lưu dữ liệu cục bộ; cần đánh giá giới hạn ghi đồng thời khi mở rộng.

## Các API quan trọng

| API | Chức năng |
| --- | --- |
| GET /health | Trạng thái, model_version, fallback_model |
| POST /api/v1/predictions | Dự đoán và lưu một phản hồi |
| POST /api/v1/predictions/batch | Tối đa 100 phản hồi theo schema |
| POST /api/v1/imports/csv | Nhập text và created_at tùy chọn |
| GET /api/v1/feedback | Danh sách có lọc và phân trang |
| GET /api/v1/dashboard/summary | Tổng hợp cảm xúc, chủ đề và ma trận |
| GET /api/v1/exports/csv hoặc pdf | Xuất dữ liệu theo bộ lọc |

Dashboard thống kê dự đoán trên phản hồi đã nhập, không hiển thị độ chính xác mô hình vì chưa có nhãn thật cho các bản ghi đó. Confidence cao cũng không biến các nhãn này thành ground truth.

## Giới hạn kỹ thuật hiện tại

UI có phân trang, bộ lọc thời gian, ma trận topic × sentiment và xuất báo cáo. PDF có biểu đồ phân bố, wrap/pagination và export limit. Browser fixture checks đã thực hiện; chưa nghiệm thu đầy đủ E2E PhoBERT/upload/export và PDF trực quan.

MODEL_BACKEND=phobert chọn hai imported task run; model nạp trong lifespan với hashes/version. Chưa có drift monitoring hoặc tự động cập nhật model.

## Kiến thức liên quan khi mở rộng

- **MLOps:** quản lý dữ liệu, thí nghiệm, artifact và phiên bản triển khai cùng nhau.
- **Data drift:** phân bố văn bản hoặc nhãn mới thay đổi; cần tập gán nhãn mới để đo ảnh hưởng thực tế.
- **Human-in-the-loop:** người phụ trách xem lại mẫu khó, sửa nhãn có kiểm duyệt.
- **Active learning:** ưu tiên chọn mẫu hữu ích để gán nhãn; cần thiết kế và đánh giá riêng.
- **Bảo vệ dữ liệu:** ẩn danh thông tin nhận dạng, giới hạn người truy cập và xác định thời hạn lưu.
- **An toàn xuất file:** CSV đã escape tiền tố công thức bảng tính; quoting đơn thuần không đủ. Giữ regression coverage khi thay export.

## Dàn ý thuyết trình 10–15 phút

| Phần | Nội dung trình bày | Bằng chứng nên đưa |
| --- | --- | --- |
| 1. Vấn đề | Khó tổng hợp phản hồi mở | Một tình huống sử dụng |
| 2. Bài toán | Hai tác vụ, các nhãn, phạm vi | Ví dụ minh họa được ghi rõ |
| 3. Dữ liệu | Nguồn, split, mất cân bằng | Thống kê từ dữ liệu thật |
| 4. Phương pháp | TF-IDF/SVM và PhoBERT | Luồng tiền xử lý, cấu hình |
| 5. Thí nghiệm | Train/validation/test, metrics | Bảng so sánh có nguồn |
| 6. Hệ thống | API, UI, lưu trữ | Demo nhập → dự đoán → dashboard |
| 7. Hạn chế | Lớp hiếm, dữ liệu gần trùng, concurrency và E2E | Metadata và phân tích lỗi |
| 8. Hướng tiếp theo | Hoàn tất E2E, vận hành và báo cáo | Kế hoạch có tiêu chí đo |

Nếu chưa có thí nghiệm thật, trình bày phần kết quả hiện tại là kiểm chứng luồng demo; không dùng F1=1,0 làm thành tích benchmark.

## Câu hỏi thường gặp khi bảo vệ

**Vì sao có baseline?** Để có mốc chất lượng và chi phí đơn giản, giúp biết mô hình phức tạp có đem lại giá trị thực nghiệm không.

**Vì sao dùng macro F1?** Vì mỗi lớp đóng góp bằng nhau, giúp nhìn thấy lớp ít mẫu bị bỏ sót. Vẫn phải báo support và F1 từng lớp.

**Vì sao cần validation nếu đã có test?** Validation phục vụ lựa chọn; test ước lượng chất lượng sau khi lựa chọn hoàn tất.

**PhoBERT có chắc tốt hơn SVM?** Không. Cần kết quả cùng dữ liệu, các tác vụ và phần cứng; độ trễ và dung lượng cũng ảnh hưởng lựa chọn.

**Confidence 90% có nghĩa gì?** Là đầu ra ước lượng của mô hình; độ tin cậy của xác suất cần được kiểm tra trên tập độc lập. Fallback từ khóa hiện không có kiểm định đó.

**Đã đạt mục tiêu đề tài chưa?** Hai F1 targets và latency HTTP tuần tự có evidence; UI E2E, vận hành và các gate nền tảng còn mở. Đối chiếu [trạng thái hiện tại](../status.md), không tự coi toàn bộ đề tài đã nghiệm thu.

## Tài liệu gốc để đọc thêm

- [UIT-VSFC — dataset của UIT NLP](https://huggingface.co/datasets/uitnlp/vietnamese_students_feedback).
- [PhoBERT — bài báo của tác giả](https://arxiv.org/abs/2003.00744).
- [PhoBERT — mã và hướng dẫn của VinAI](https://github.com/VinAIResearch/PhoBERT).
- [Scikit-learn — biểu diễn văn bản](https://scikit-learn.org/stable/modules/feature_extraction.html).
- [Scikit-learn — hiệu chuẩn xác suất](https://scikit-learn.org/stable/modules/calibration.html).

Các nguồn giải thích lý thuyết và giao diện thư viện. Cấu hình, kết quả và mức hoàn thiện riêng của đề tài phải đối chiếu mã nguồn và log thí nghiệm của dự án.
