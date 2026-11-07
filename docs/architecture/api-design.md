# API design

Base URL local: `http://localhost:8000`. Contract máy đọc được tại `/openapi.json`; Swagger tại `/docs`. Các route hiện tại giữ prefix `/api/v1` và HTTP 200 cho thao tác thành công để tương thích UI.

## Quy tắc chung

- JSON request/response dùng UTF-8. Date input phải có timezone; service lưu UTC với độ chính xác microsecond. CSV không chấp nhận ngày giờ naive.
- `text` có 1–5000 ký tự và không được chỉ có whitespace. Giữ `raw_text` nguyên bản; `text` trong response là NFC + collapsed whitespace.
- Sentiment: negative/neutral/positive. Topic: lecturer/training_program/facility/others. Filter sai enum trả 422.
- Server sinh `X-Request-ID` cho response và log method/path/status/duration; không log request body, query values hay Authorization.
- Nếu cấu hình `API_TOKEN`, mọi `/api/v1` yêu cầu `Authorization: Bearer <token>`. Health, readiness và docs là public. Không có users/RBAC hoặc multi-tenant isolation trong bản này.
- Validation error trả `{"detail":[{"loc":[],"type":"...","msg":"..."}]}` mà không echo input. Các lỗi khác trả `{"detail":"thông báo"}`; 401 có `WWW-Authenticate: Bearer`, lỗi nội bộ không lộ chi tiết.

| Status | Ý nghĩa                                                        |
| ------ | -------------------------------------------------------------- |
| 200    | Thành công                                                     |
| 401    | Thiếu/sai bearer credential khi bật auth                       |
| 404    | Không có feedback ID                                           |
| 413    | Vượt giới hạn request/upload/row/export                        |
| 422    | Request, CSV hoặc date/filter không hợp lệ                     |
| 500    | Lỗi model/database/nội bộ được che chi tiết                    |
| 503    | DB đang locked, readiness thất bại hoặc chưa cấu hình font PDF |

Request body được giới hạn trước parsing ở `MAX_CSV_BYTES + 65536` bytes cho POST/PUT/PATCH; riêng nội dung file CSV có giới hạn chính xác `MAX_CSV_BYTES`. Đây không thay thế timeout/connection limits ở reverse proxy.

## Prediction

`POST /api/v1/predictions`

```json
{
  "text": "  Giảng viên   nhiệt tình  ",
  "created_at": "2026-11-06T09:00:00+07:00"
}
```

Response minh họa, không phải kết quả đo:

```json
{
  "feedback_id": 1,
  "raw_text": "  Giảng viên   nhiệt tình  ",
  "text": "Giảng viên nhiệt tình",
  "sentiment_label": "positive",
  "sentiment_confidence": 0.8,
  "topic_label": "lecturer",
  "topic_confidence": 0.9,
  "model_version": "example-v1",
  "predicted_at": "2026-11-06T02:00:00Z"
}
```

`created_at` tùy chọn. Extra JSON fields bị từ chối. Predictor contract được kiểm tra trước khi ghi nhãn/confidence vào DB.

`POST /api/v1/predictions/batch` nhận `{"items":[{"text":"..."}]}`, 1–100 phần tử. Response là array cùng thứ tự. Inference hoàn tất trước khi lấy DB writer lock; nếu inference hoặc transaction thất bại, không lưu một phần batch. Không có idempotency key: retry có thể tạo dữ liệu trùng.

## CSV import

`POST /api/v1/imports/csv`, multipart field `file`, filename `.csv`, encoding UTF-8 hoặc UTF-8 BOM. Header bắt buộc `text`, tùy chọn `created_at`; header trùng bị từ chối. Các cột bổ sung được bỏ qua nếu số cột khớp header.

Giới hạn mặc định: file 2 MiB và 1000 data records. Kiểm tra toàn bộ file trước khi inference/persist. Nếu vượt giới hạn hoặc CSV malformed thì không ghi dòng nào. Dòng sai schema được loại và báo lỗi; tất cả dòng hợp lệ được persist trong một transaction. Lỗi model/database làm cả nhóm hợp lệ rollback, không chuyển thành row error.

```json
{
  "imported": 1,
  "errors": [{ "row": 2, "message": "Nội dung phản hồi không được để trống." }]
}
```

`row` là số thứ tự data record cộng header, bắt đầu 2; không phải physical line number của file có quoted multiline fields. Nếu mọi record sai, imported=0 và có errors; file chỉ có header trả 422.

## Feedback và dashboard

`GET /api/v1/feedback`: `page` mặc định 1, `page_size` mặc định 20 và tối đa 100. SQL `COUNT` + `LIMIT/OFFSET` trong read transaction; thứ tự `id DESC`. Response gồm items, total, page, page_size.

`GET /api/v1/feedback/{id}` trả một record: id, raw_text, text, source, created_at, received_at, hai nhãn/confidence, model_version, predicted_at. Không có PATCH/DELETE hoặc re-predict endpoint trong MVP.

`GET /api/v1/dashboard/summary`: total, sentiment counts, topic counts, matrix topic × sentiment, has_timestamps. Counts do SQL aggregation; has_timestamps chỉ phản ánh có source-created timestamp hay không.

Các read/export route dùng chung filters:

| Query          | Semantics                                          |
| -------------- | -------------------------------------------------- |
| sentiment      | Enum cảm xúc                                       |
| topic          | Enum chủ đề                                        |
| predicted_from | Inclusive lower bound theo thời điểm dự đoán       |
| predicted_to   | Exclusive upper bound; phải lớn hơn predicted_from |

Hai date query cần timezone, được chuyển UTC trước so sánh. Không dùng date range này để lọc created_at hoặc suy diễn mốc học kỳ. Pagination dạng offset phù hợp MVP; cursor pagination là extension khi dữ liệu lớn. Nhiều page request riêng không tạo một snapshot cố định trước các insert mới.

## Export

`GET /api/v1/exports/csv` hoặc `/pdf`, cùng filters. Tối đa `MAX_EXPORT_ROWS` (mặc định 5000). Nếu nhiều hơn, trả 413 và yêu cầu thu hẹp filter; không cắt âm thầm.

CSV có BOM, raw/normalized text, nhãn/confidence, source và timestamps. Các cell có khả năng thành spreadsheet formula được thêm apostrophe; giá trị file export có thể khác text raw lưu trong DB để an toàn khi mở bằng bảng tính. PDF wrap nội dung đầy đủ và tự ngắt trang; cần Unicode font được cấu hình hoặc font mặc định có sẵn. PDF có hai biểu đồ phân bố tính từ cùng tập bản ghi được xuất.

## Operations

`GET /health`: status, model_version, fallback_model. `fallback_model=false` không chứng minh model được đánh giá tốt hoặc có dữ liệu đại diện.

`GET /ready`: 200 khi model đã lắp trong lifespan và DB kết nối được; 503 nếu DB không sẵn sàng. Model thiếu/không hợp lệ trong chế độ yêu cầu model sẽ làm startup thất bại, thay vì trả ready sai.

## Compatibility và giới hạn

Giữ endpoint, field dự đoán cũ và default query. Thêm raw_text/received_at và detail endpoint là additive. Thắt validation naive date/unknown fields/invalid filter là thay đổi có chủ ý, cần cập nhật caller đang gửi dữ liệu đó. Batch trước đây có thể ghi một phần; hiện atomic. Các Python helper được re-export từ main.py cũ là nội bộ và đã được thay bằng app factory/services; entry point ASGI vẫn giữ nguyên.

Auth một token dành cho API nội bộ; UI hiện tại không quản lý token. Chế độ local không token vẫn tương thích. Public web cần OIDC/BFF hoặc một luồng login/session được thiết kế riêng, không nhúng shared API token trong frontend.
