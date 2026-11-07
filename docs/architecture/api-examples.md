# Ví dụ API

Xem [API design](api-design.md) cho đầy đủ hợp đồng và [Swagger local](http://localhost:8000/docs) khi API đang chạy. Ví dụ là minh họa, không phải kết quả benchmark.

## Single prediction

```http
POST /api/v1/predictions
Content-Type: application/json

{"text":"Giảng viên nhiệt tình, nhưng phòng máy cần nâng cấp.","created_at":"2026-11-06T09:00:00+07:00"}
```

Response giữ nhãn/confidence/model_version/feedback_id/predicted_at và thêm raw_text; text đã được chuẩn hóa. Nếu bật API_TOKEN, thêm Authorization: Bearer với credential của môi trường nội bộ; không chép secret vào tài liệu hoặc frontend.

## Ordered atomic batch

```json
{"items":[{"text":"Cô giảng dễ hiểu"},{"text":"Wifi quá yếu"}]}
```

Tối đa 100 items. Toàn batch không persist nếu inference hoặc database transaction thất bại.

## SQL pagination và filters

```http
GET /api/v1/feedback?page=1&page_size=20&sentiment=negative&topic=facility
GET /api/v1/dashboard/summary?sentiment=negative
GET /api/v1/feedback/1
```

Date range dùng predicted_from/predicted_to có timezone; truyền bằng URLSearchParams để encode dấu + đúng. Summary và export dùng cùng filters, nhưng page/page_size chỉ áp dụng cho list.
