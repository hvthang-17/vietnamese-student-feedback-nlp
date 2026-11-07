# 05. Đánh giá mô hình và phân tích lỗi

[Chỉ mục](README.md) · [Tiếp: Hệ thống và trình bày](06-system-and-presentation.md)

## Metrics cơ bản

Với một lớp đang xét, TP là dự đoán đúng lớp đó, FP là gán nhầm lớp khác thành lớp đó, FN là bỏ sót mẫu thực thuộc lớp đó.

- Precision = TP/(TP+FP): các mẫu dự đoán thuộc lớp có bao nhiêu mẫu đúng.
- Recall = TP/(TP+FN): tìm được bao nhiêu mẫu thực thuộc lớp.
- F1 = 2PR/(P+R): trung bình điều hòa của precision và recall.
- Accuracy = số dự đoán đúng/tổng số mẫu.
- Macro F1 = trung bình F1 của các lớp với trọng số bằng nhau.
- Weighted F1 = trung bình F1 có trọng số theo support, tức số mẫu thực của từng lớp.

Ví dụ minh họa: TP=8, FP=2, FN=4 cho precision=0,80, recall≈0,67 và F1≈0,73. Đây không phải kết quả của artifact hiện tại. Khi mẫu số bằng 0 cần quy ước và báo rõ; reporter mới quy ước precision/recall/F1 bằng 0 khi mẫu số bằng 0 và luôn tính đủ các lớp trong mapping.

Với lớp phổ biến áp đảo, accuracy cao vẫn có thể đi cùng F1 lớp hiếm thấp. Vì vậy đề tài ưu tiên macro F1, nhưng vẫn phải xem từng lớp và support. Không gộp cảm xúc và chủ đề thành một F1 chung nếu chưa định nghĩa cách tính.

## Confusion matrix và joint accuracy

Trong ma trận, cần ghi rõ hàng là nhãn thật, cột là nhãn dự đoán và thứ tự nhãn. Ô ngoài đường chéo cho biết cặp lớp hay nhầm. ml/evaluation/metrics.py dùng thứ tự ID từ labels.py.

Joint accuracy có thể bổ sung để đo tỷ lệ phản hồi mà cả cảm xúc lẫn chủ đề đều đúng. Nó khác accuracy riêng từng tác vụ và hiện chưa được reporter tính.

## Rò rỉ dữ liệu

Leakage là thông tin không hợp lệ từ quá trình đánh giá đi vào huấn luyện/lựa chọn. Ví dụ: fit TF-IDF trên cả test, cùng câu nằm ở train và test, hoặc điều chỉnh mô hình nhiều lần theo điểm test. Seed khác nhau không bảo đảm các tập độc lập khi cùng sinh từ kho template.

Hiện baseline_metrics.json ghi data_source=canonical_local_seed và test chỉ có 800 mẫu. Khi tái tạo loader cũ với seed 42/43/44, có 774/800 câu test xuất hiện nguyên văn trong train. Số đo này giải thích nguy cơ điểm 1,0 quá lạc quan; không phải phép đánh giá độ trùng của UIT-VSFC thật.

## Calibration, độ trễ và bất định

Một xác suất lớn chưa đủ chứng minh dự đoán đúng. Có thể dùng reliability diagram và Brier/log loss để đánh giá xác suất; các kiểm tra này chưa được dự án báo cáo. Nếu dùng ngưỡng chuyển người xem xét, chọn ngưỡng trên validation và đo tác động đến coverage/lỗi.

Latency cần phân biệt thời gian nạp model, suy luận đã warmup và toàn request gồm validation, suy luận, ghi database. p95 là ngưỡng mà khoảng 95% mẫu đo không vượt quá, không phải thời gian lớn nhất. Công bố số mẫu, warmup, batch size, CPU/GPU và mức đồng thời để người khác diễn giải đúng.

## Phân tích lỗi có hệ thống

Thu thập ít nhất 10 lỗi tiêu biểu sau đánh giá cuối. Ghi văn bản đã ẩn danh, nhãn thật, nhãn dự đoán, confidence, loại lỗi và giả thuyết. Nhóm lỗi có thể gồm phủ định, viết tắt, đa chủ đề, mỉa mai, thiếu ngữ cảnh hoặc nhãn không nhất quán.

| Mẫu | Nhãn thật | Dự đoán | Nhóm lỗi | Bước kiểm tra |
| --- | --- | --- | --- | --- |
| Ví dụ minh họa: “không có gì để chê” | Do người gán nhãn xác định | Điền sau khi chạy | Phủ định phức hợp | So sánh token/đặc trưng |

Không thay nhãn chuẩn chỉ vì mô hình dự đoán khác. Nếu phát hiện nhãn đáng nghi, ghi lại quy trình xem xét riêng. Dùng lỗi test để nêu giới hạn; các cải tiến sau đó cần một vòng đánh giá độc lập mới.

## Điều kiện trước khi công bố kết quả

Xác nhận nguồn dữ liệu thật; số mẫu thực từng split; không fit preprocessing vào test; cấu hình đã chốt; đủ metrics từng lớp; cùng quy trình cho hai mô hình; số đo latency đúng phạm vi; không dùng số minh họa thay kết quả. Các cờ all_criteria_met trong báo cáo hiện chỉ phản ánh các phép so sánh số học, không xác nhận nguồn dữ liệu hợp lệ.

Pipeline hiện tại đã bỏ synthetic fallback và metric mặc định. Đọc [workflow](../../ml/README.md) để tạo lại kết quả; số liệu cũ ở trên chỉ giải thích giới hạn của thí nghiệm lịch sử.
