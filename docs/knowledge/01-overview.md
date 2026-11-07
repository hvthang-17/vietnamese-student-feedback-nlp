# 01. Tổng quan đề tài

[Chỉ mục](README.md) · [Tiếp: Kiến thức nền](02-foundations.md)

## Vấn đề cần giải quyết

Phản hồi mở chứa thông tin về giảng dạy, chương trình và điều kiện học tập. Đọc thủ công nhiều phản hồi mất thời gian và khó tổng hợp nhất quán. Hệ thống gán nhãn để hỗ trợ người phụ trách tìm nhóm vấn đề cần đọc kỹ hơn.

Đầu vào là một câu hoặc đoạn phản hồi tiếng Việt. Đầu ra gồm một nhãn cảm xúc, một nhãn chủ đề, confidence cho từng tác vụ và phiên bản mô hình. Ví dụ minh họa: “Wifi phòng máy yếu” có thể được gán negative/facility. Đây không phải dự đoán được đo trong tài liệu.

## Hai tác vụ học có giám sát

| Tác vụ | ID và nhãn trong dự án |
| --- | --- |
| Cảm xúc | 0 negative; 1 neutral; 2 positive |
| Chủ đề | 0 lecturer; 1 training_program; 2 facility; 3 others |

Mỗi tác vụ là phân loại đa lớp với một nhãn cho mỗi mẫu. Dự án huấn luyện hai bộ phân loại riêng, không phải mô hình đa nhiệm dùng chung encoder. Hai đầu ra cũng không biến tác vụ thành phân loại nhiều nhãn trong từng nhóm.

Một phản hồi như “Thầy dạy hay nhưng phòng nóng” có nhiều khía cạnh. Thiết kế một chủ đề và một cảm xúc cho cả câu không biểu diễn hết sắc thái này. Phân tích cảm xúc theo khía cạnh là hướng mở rộng, chưa có trong hệ thống.

## Dữ liệu UIT-VSFC

Theo cấu hình dự án, số mẫu kỳ vọng là train 11.426, validation 1.583, test 3.166, tổng 16.175. Snapshot hiện có đã được kiểm đếm theo manifest; khi tải snapshot mới phải kiểm tra lại số đếm, việc khai báo số mẫu trong config không chứng minh dữ liệu đã được kiểm định. Dataset có các trường sentence, sentiment và topic. Xem [dataset do UIT NLP công bố](https://huggingface.co/datasets/uitnlp/vietnamese_students_feedback).

Train dùng để học tham số, validation để lựa chọn cấu hình, test để đánh giá cấu hình cuối cùng. Dữ liệu mới từ giao diện được lưu vào SQLite phục vụ dashboard, không tự động trở thành dữ liệu huấn luyện có nhãn chuẩn.

## Phạm vi hiện tại

Dữ liệu chính thức, baseline và hai checkpoint PhoBERT đã có bằng chứng thực nghiệm. Backend có adapter PhoBERT CPU và UI Góc lắng nghe. Artifact legacy canonical_local_seed được giữ riêng, không dùng nghiệm thu. Đọc [trạng thái hiện tại](../status.md) để biết giới hạn và kết quả mới nhất.

Mục tiêu trong PRD là macro F1 cảm xúc ≥ 0,80; chủ đề ≥ 0,75 và độ trễ p95 dưới 2 giây. Đây là tiêu chí mong muốn, không phải thành tích đã xác nhận.

## Giá trị và giới hạn ứng dụng

Nhãn giúp tổng hợp phân bố và tìm phản hồi cần xem lại. Confidence không xác nhận tính đúng đắn của nội dung phản hồi. Tỷ lệ tiêu cực trong tập nhập chỉ mô tả tập đó, không tự suy rộng cho toàn trường khi mẫu khảo sát thiếu đại diện. Không dùng dự đoán để tự động đánh giá hoặc kỷ luật cá nhân.
