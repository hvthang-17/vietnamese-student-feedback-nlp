# Quy trình xử lý NLP cho phản hồi sinh viên tiếng Việt

Tài liệu này giải thích cách thực hiện bài toán từ dữ liệu đến dự đoán. Đây là hướng dẫn phương pháp và điều kiện nghiệm thu, không phải bằng chứng các bước đã được chạy hoặc mô hình đã đạt mục tiêu. Mọi câu, nhãn và xác suất ví dụ bên dưới đều là minh họa.

Đọc thêm: [kiến thức nền](../knowledge/02-foundations.md), [mô hình](../knowledge/03-models.md), [đánh giá](../knowledge/05-evaluation.md), [lệnh thực thi](../../ml/README.md), [kiến trúc hệ thống](../architecture/system-design.md).

## 1. Xác định đầu vào, đầu ra và phạm vi

Đầu vào là một câu hoặc đoạn phản hồi tiếng Việt. Đầu ra có hai nhóm nhãn:

| Tác vụ | ID và nhãn | Ý nghĩa |
| --- | --- | --- |
| Cảm xúc | 0 negative; 1 neutral; 2 positive | Thái độ tiêu cực, trung tính hoặc tích cực |
| Chủ đề | 0 lecturer; 1 training_program; 2 facility; 3 others | Nội dung phản hồi thuộc lĩnh vực nào |

Ví dụ: “Giảng viên hướng dẫn nhiệt tình, bài giảng dễ hiểu.” có thể được gán positive/lecturer. Nhãn thật của dữ liệu nghiên cứu phải lấy từ annotation, không suy ra từ dự đoán của model.

Mỗi phản hồi nhận một nhãn cho mỗi tác vụ. Thiết kế dùng hai classifier độc lập, không phải phân tích cảm xúc theo từng khía cạnh. “Thầy dạy hay nhưng phòng học quá nóng” chứa nhiều khía cạnh, nên thiết kế hiện tại không biểu diễn đầy đủ mọi cảm xúc và chủ đề trong câu.

**Điều kiện hoàn thành:** xác định rõ đơn vị dự đoán, label mapping, trường hợp khó và giới hạn một nhãn mỗi tác vụ; các thành phần xử lý cùng hiểu một bộ nhãn.

## 2. Phân biệt huấn luyện và suy luận

```text
HUẤN LUYỆN OFFLINE
Dữ liệu có nhãn → kiểm định → preprocessing → biểu diễn số
→ học trên train → chọn bằng validation → đánh giá test → lưu artifact

SUY LUẬN ONLINE
Phản hồi mới → validate → preprocessing giống lúc train
→ vectorizer/tokenizer đã lưu → model đã học → nhãn/confidence → lưu DB/UI
```

Không train lại cho mỗi request. Dataset nghiên cứu có nhãn chuẩn; phản hồi từ giao diện chỉ có nhãn dự đoán, không tự trở thành ground truth để tái huấn luyện.

## 3. Thu thập và kiểm định dữ liệu

Sử dụng UIT-VSFC theo phạm vi đề tài. Mỗi mẫu cần có văn bản, sentiment và topic. Xác định nguồn, revision và điều kiện sử dụng trước khi làm thí nghiệm chính thức.

Các bước:

1. Nạp đúng các split đã công bố, không tự trộn lại cho tiện.
2. Kiểm tra trường dữ liệu, kiểu dữ liệu, nhãn ngoài phạm vi và văn bản rỗng.
3. Đếm số mẫu thực tế; số mẫu kỳ vọng theo cấu hình là train 11.426, validation 1.583 và test 3.166.
4. Kiểm tra trùng trong từng split và giữa các split; đánh giá thêm near duplicates nếu cần.
5. Ghi manifest và checksum để những lần thí nghiệm sau dùng đúng snapshot.

Không dùng các con số kỳ vọng để thay số đo thực. Không tự sinh mẫu khi tải dataset thất bại rồi gọi đó là UIT-VSFC. Nếu bộ chuẩn có câu trùng, công bố kết quả kiểm tra và protocol xử lý; không âm thầm xóa hoặc đổi split rồi vẫn so sánh như benchmark chuẩn.

**Đầu ra:** snapshot và báo cáo kiểm định dữ liệu.

**Điều kiện hoàn thành:** truy vết được nguồn/revision; schema/nhãn/số mẫu đã kiểm tra; lỗi dữ liệu được giải quyết hoặc ghi rõ; không có fallback synthetic trong thí nghiệm chính thức.

## 4. Giữ đúng vai trò train, validation và test

| Split | Được sử dụng để | Không được sử dụng để |
| --- | --- | --- |
| Train | Học vocabulary, IDF, trọng số classifier/encoder | Thay thế đánh giá tổng quát hóa |
| Validation | Chọn n-gram, C, class weight, learning rate, checkpoint và ngưỡng | Báo cáo như test độc lập cuối cùng |
| Test | Đo cấu hình cuối đã chốt | Liên tục tuning preprocessing hoặc model |

Ví dụ, chọn C của SVM bằng validation, sau đó đánh giá cấu hình cuối trên test. Khám phá lỗi test rồi sửa model và đo lại cùng test không tạo ra một đánh giá độc lập mới.

Nếu calibration dùng cross-validation nội bộ, vectorizer và classifier phải được fit trong từng train fold tương ứng. Không fit IDF trước trên toàn bộ dữ liệu rồi coi các fold hiệu chuẩn là hoàn toàn độc lập.

**Điều kiện hoàn thành:** chốt protocol lựa chọn và đánh giá trước lần chạy cuối; không có thông tin validation/test đi vào bước fit không phù hợp.

## 5. EDA: hiểu dữ liệu trước khi chọn preprocessing

| Phân tích | Câu hỏi cần trả lời | Quyết định hỗ trợ |
| --- | --- | --- |
| Phân bố sentiment/topic | Lớp nào ít mẫu, lớp nào áp đảo? | Chọn metrics và khảo sát class weight |
| Độ dài phản hồi | Câu thường ngắn hay dài? | Khảo sát max_length và truncation |
| Viết tắt, lỗi chính tả | Có gv, ko, từ lóng hoặc lỗi dấu không? | Thiết kế ablation phù hợp |
| Trùng/gần trùng | Mô hình có thể ghi nhớ câu đã gặp không? | Công bố giới hạn đánh giá |
| Ma trận topic × sentiment | Các tổ hợp nhãn phân bố ra sao? | Hiểu dữ liệu và lỗi từng nhóm |

Có thể kiểm định schema/counts cả ba split, nhưng nên dùng train để khám phá từ vựng và quyết định đặc trưng. Số đơn vị tách bằng whitespace không đồng nghĩa số từ đã được tách từ tiếng Việt.

**Đầu ra:** EDA có số liệu thực, biểu đồ/bảng và nhận xét dẫn đến quyết định thí nghiệm.

**Điều kiện hoàn thành:** không có thống kê ước lượng được trình bày như phép đo; nêu rõ mất cân bằng và các rủi ro đối với lớp ít mẫu.

## 6. Chuẩn hóa văn bản và giữ bản gốc

Ví dụ:

```text
raw_text:        "  Giảng viên    nhiệt tình,\n bài giảng dễ hiểu!  "
normalized_text: "Giảng viên nhiệt tình, bài giảng dễ hiểu!"
```

Thứ tự xử lý cơ bản:

1. Kiểm tra chuỗi không rỗng và không vượt giới hạn.
2. Chuẩn hóa Unicode NFC để thống nhất biểu diễn ký tự tiếng Việt.
3. Bỏ whitespace đầu/cuối và gộp tab/newline/khoảng trắng liên tiếp.
4. Giữ dấu tiếng Việt, dấu câu và các từ có nghĩa.
5. Giữ raw text riêng để truy vết; không ghi đè bản gốc bằng bản chuẩn hóa.

Không xóa phủ định: “không tốt” không được biến thành “tốt”. Không mặc định xóa stopwords, emoji, chuyển toàn bộ viết tắt hoặc lowercase cho mọi loại model. Những bước bổ sung phải được khảo sát bằng validation và ghi vào config.

**Điều kiện hoàn thành:** có test Unicode/whitespace/chuỗi rỗng và giới hạn độ dài; cùng quy tắc chuẩn hóa được dùng trong train và inference. Với dữ liệu lịch sử chỉ còn text chuẩn hóa, không tuyên bố đã khôi phục raw text.

## 7. Biểu diễn đầu vào cho baseline

Máy học truyền thống không nhận trực tiếp chuỗi văn bản. Luồng baseline là:

```text
Normalized text → token/n-gram → TF-IDF vector → Linear SVM
```

Với câu “giảng viên nhiệt tình”, nếu dùng tokenization theo khoảng trắng:

- Unigram: giảng, viên, nhiệt, tình.
- Bigram: giảng viên, viên nhiệt, nhiệt tình.

Đây là minh họa đặc trưng, không phải kết quả từ tokenizer PhoBERT. Có thể khảo sát character n-gram để bắt biến thể ký tự, nhưng chỉ giữ khi validation chứng minh có ích.

TF-IDF kết hợp mức xuất hiện trong câu với mức phổ biến trên tập train để tạo vector thưa. Phải học vocabulary/IDF trên train; validation/test chỉ dùng transform của vectorizer đã fit.

**Đầu ra:** vectorizer và ma trận đặc trưng cho từng split, với cấu hình n-gram/min_df/max_df được ghi lại.

**Điều kiện hoàn thành:** vectorizer không được fit trên validation/test; vectorizer đã lưu có thể biến đổi văn bản mới theo cùng cách.

## 8. Huấn luyện hai baseline classifier

```text
TF-IDF → SVM cảm xúc: 3 lớp
TF-IDF → SVM chủ đề: 4 lớp
```

Các bước thực hiện:

1. Chọn cấu hình ban đầu đủ đơn giản.
2. Khảo sát n-gram, C và class weight theo kế hoạch đã chốt.
3. Dùng validation macro F1 để lựa chọn.
4. Fit pipeline cuối và calibration nếu cần xuất confidence.
5. Lưu cả vectorizer, estimator, label mapping và config.

Class weight điều chỉnh mức phạt, không sinh thêm dữ liệu. Calibration biến decision scores thành ước lượng xác suất; nó không tự bảo đảm mọi confidence đều đúng.

**Điều kiện hoàn thành:** hai pipeline nạp lại được, dự đoán đúng schema/nhãn, có tuning log và đánh giá pipeline cuối. Chưa đạt F1 mục tiêu vẫn phải lưu kết quả thật; không sửa metrics để nghiệm thu.

## 9. Chuẩn bị đầu vào và fine-tune PhoBERT

```text
Normalized text → Vietnamese word segmentation → checkpoint tokenizer
→ token IDs + attention mask → PhoBERT encoder → classification head
```

Tách từ và subword tokenization là hai bước khác nhau. Trong hướng triển khai của đề tài, PyVi phục vụ tách từ, còn tokenizer phải đi cùng checkpoint đã chọn. Không tự tách khoảng trắng rồi gọi đó là tokenizer PhoBERT.

Các bước:

1. Chọn checkpoint và pin model revision.
2. Chốt preprocessing, segmenter và max_length bằng dữ liệu train/validation.
3. Tokenize, truncation và padding theo cấu hình thống nhất.
4. Train riêng sentiment và topic, sử dụng seed đã ghi.
5. Chọn checkpoint theo validation macro F1; dùng early stopping theo protocol.
6. Lưu model, tokenizer, preprocessing config, logs và metrics.

Chọn checkpoint tốt nhất và early stopping không phải cùng một việc: một bước chọn trạng thái, một bước quyết định dừng huấn luyện. Không chọn checkpoint bằng test.

**Điều kiện hoàn thành:** hai tác vụ có checkpoint sử dụng lại được; tokenization/inference tái tạo đúng preprocessing; có bằng chứng huấn luyện và đánh giá, không chỉ có file code.

## 10. Đánh giá cuối và phân tích lỗi

| Chỉ số | Ý nghĩa |
| --- | --- |
| Accuracy | Tỷ lệ dự đoán đúng |
| Precision | Dự đoán thuộc một lớp có bao nhiêu mẫu đúng |
| Recall | Tìm được bao nhiêu mẫu thực thuộc lớp đó |
| F1 từng lớp | Cân bằng precision và recall |
| Macro F1 | Trung bình F1 với trọng số bằng nhau giữa các lớp |
| Weighted F1 | Trung bình F1 có trọng số theo support |
| Confusion matrix | Những cặp nhãn bị nhầm |

Báo cáo đủ từng lớp kể cả lớp ít mẫu; công bố quy ước khi mẫu số bằng 0. Không gộp sentiment và topic thành một F1 duy nhất mà không định nghĩa phép tính.

Đọc các lỗi đại diện và nhóm chúng theo phủ định, viết tắt, đa chủ đề, cảm xúc pha trộn, thiếu ngữ cảnh hoặc nghi vấn annotation. Ghi nhãn thật/dự đoán/confidence và giả thuyết; không sửa nhãn chuẩn chỉ vì model không đồng ý.

**Điều kiện hoàn thành:** có metrics cho cả hai tác vụ, confusion matrix và ít nhất 10 lỗi đại diện nếu có; mọi kết luận đi kèm bằng chứng. Dùng lỗi test để trình bày giới hạn, không ngầm biến test thành validation.

## 11. So sánh và lựa chọn mô hình

Baseline và PhoBERT phải được so sánh trên cùng split, cùng metrics và phạm vi benchmark rõ ràng. Bảng cần có macro/weighted F1, accuracy, F1 lớp ít mẫu, CPU latency, dung lượng và tài nguyên vận hành.

Lựa chọn cấu hình/model theo protocol validation đã chốt; dùng test cuối để báo cáo và kiểm tra mục tiêu, không liên tục chọn lại theo test. Không mặc định PhoBERT phù hợp hơn vì phức tạp hơn.

Mục tiêu PRD là macro F1 cảm xúc ≥0,80, chủ đề ≥0,75 và API p95 <2 giây trên máy demo công bố. Đây là mục tiêu dự kiến, không phải thành tích hiện có. Inference latency không bao gồm DB/HTTP không được coi là latency toàn API.

**Điều kiện hoàn thành:** quyết định model có lý do, so sánh công bằng và công bố cả kết quả không đạt. Nếu chọn loại model chưa có adapter phục vụ, phải hoàn thiện adapter trước nghiệm thu triển khai.

## 12. Đóng gói và suy luận online

```text
Input mới → validate → giữ raw text → normalize
→ vectorizer/tokenizer đã lưu → hai model → kiểm tra output contract
→ transaction lưu feedback + prediction → response → dashboard
```

Gói baseline cần vectorizer và classifier; gói PhoBERT cần checkpoint, tokenizer và preprocessing/segmentation config. Cả hai cần label mapping và model version.

Chỉ promote một run đã review, không tự thay model API sau mỗi lần train. Không nạp artifact không tin cậy. Health/readiness và schema output giúp kiểm tra luồng, không chứng minh model đạt chất lượng học thuật.

Ví dụ response minh họa:

```json
{
  "raw_text": "  Giảng viên   dễ hiểu  ",
  "text": "Giảng viên dễ hiểu",
  "sentiment_label": "positive",
  "sentiment_confidence": 0.8,
  "topic_label": "lecturer",
  "topic_confidence": 0.9,
  "model_version": "example-v1"
}
```

Confidence không phải phần trăm hài lòng hay bảo đảm dự đoán đúng cho câu đó. Mức độ tin cậy của xác suất cần được kiểm định riêng.

**Điều kiện hoàn thành:** model nạp lại được, online preprocessing khớp training, API trả đúng contract, raw/normalized text được lưu đúng và inference không kích hoạt retraining.

## 13. Checklist tổng kết quy trình

- [ ] Chốt nhãn, đơn vị dự đoán và giới hạn bài toán.
- [ ] Dùng dataset thật, kiểm tra split/schema/nhãn và lưu provenance.
- [ ] EDA dựa trên phép đo, công bố mất cân bằng và độ trùng.
- [ ] Giữ raw text; chuẩn hóa tiếng Việt nhất quán, không làm đảo nghĩa.
- [ ] Baseline fit đặc trưng đúng phạm vi train và lưu pipeline đầy đủ.
- [ ] PhoBERT dùng checkpoint/tokenizer pin, segmentation và validation selection rõ ràng.
- [ ] Test chỉ đánh giá cấu hình cuối, không phục vụ tuning lặp lại.
- [ ] Báo cáo metrics từng lớp và phân tích lỗi, không tạo điểm thay thế khi thiếu kết quả.
- [ ] So sánh chất lượng/tài nguyên/latency cùng phạm vi trước chọn model.
- [ ] Đóng gói và suy luận tái tạo pipeline training, không train trong request.

Các checkbox là điều kiện cần xác minh trong tương lai, chưa được đánh dấu hoàn thành bởi việc viết tài liệu. Lệnh chạy và cấu trúc output được duy trì tại [ml/README.md](../../ml/README.md), tránh sao chép nhiều phiên bản lệnh trong tài liệu lý thuyết.
