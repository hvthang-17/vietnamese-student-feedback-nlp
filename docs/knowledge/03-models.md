# 03. Các mô hình trong đề tài

[Chỉ mục](README.md) · [Tiếp: Quy trình](04-workflow.md)

## Baseline TF-IDF + Linear SVM

Luồng xử lý: văn bản chuẩn hóa → vector TF-IDF → SVM tuyến tính → hiệu chuẩn điểm số → nhãn và confidence. Dự án có hai pipeline riêng cho cảm xúc và chủ đề.

TF đo tần suất trong văn bản; IDF làm giảm trọng số token xuất hiện ở nhiều tài liệu. Một cách viết với smoothing là idf(t) = log((1 + N)/(1 + df(t))) + 1. N là số tài liệu train, df(t) là số tài liệu chứa token t. Vectorizer còn có chuẩn hóa vector và cấu hình TF riêng; xem [tài liệu chính thức TF-IDF](https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting).

Linear SVM học các ranh giới tuyến tính trong không gian đặc trưng, ưu tiên biên phân tách lớn và đánh đổi với lỗi huấn luyện qua C. Tăng C thường phạt lỗi mạnh hơn, nhưng không bảo đảm điểm validation tốt hơn.

### Cấu hình đang dùng

| Thành phần | Cấu hình trong ml/training/baseline.py |
| --- | --- |
| Word TF-IDF | ngram_range=(1,2), min_df=2, max_df=0.95, sublinear_tf=True |
| Char TF-IDF tùy chọn | ngram_range=(3,5), min_df=5, max_df=0.95 |
| Chọn char n-gram | Chỉ thêm nếu macro F1 validation tăng hơn 0,002 trong phép so sánh ban đầu |
| Tìm cấu hình | C thuộc 0,5/1/2; class_weight balanced hoặc None |
| Hiệu chuẩn | CalibratedClassifierCV, cv=3, sigmoid |

Char n-gram có thể bắt một phần biến thể ký tự, nhưng cũng tăng số đặc trưng. Class weight điều chỉnh mức phạt theo lớp; không tạo thêm mẫu thiểu số. Ablation là thay đổi một thành phần để quan sát đóng góp, cần giữ các điều kiện còn lại nhất quán.

### Confidence và calibration

LinearSVC không tự xuất xác suất; wrapper hiệu chuẩn chuyển điểm quyết định thành ước lượng xác suất. Calibration tốt nghĩa là trong nhiều dự đoán khoảng 0,8, tỷ lệ đúng quan sát được gần 80%. Đây là tính chất trên một tập dự đoán, không phải bảo đảm một câu cụ thể đúng 80%.

Hiệu chuẩn cần dữ liệu độc lập với bước fit classifier bên trong mỗi fold. Pipeline mới bọc cả TF-IDF và LinearSVC trong CalibratedClassifierCV; vocabulary/IDF được học riêng cho mỗi fold, validation/test bên ngoài vẫn tách riêng. Xem [hướng dẫn calibration](https://scikit-learn.org/stable/modules/calibration.html).

## Transformer và PhoBERT

Transformer dùng self-attention để trao đổi thông tin giữa vị trí token. Attention tạo trọng số từ mức tương thích giữa query và key rồi kết hợp value; khái quát Attention(Q,K,V) = softmax(QKᵀ/√d) V. Attention không tự tạo ra nhãn; mô hình phân loại cần một classification head và được fine-tune với nhãn tác vụ.

PhoBERT là mô hình ngôn ngữ tiền huấn luyện cho tiếng Việt. Đề tài dùng vinai/phobert-base. Tiền huấn luyện học biểu diễn từ ngữ liệu lớn; fine-tune cập nhật mô hình trên phản hồi có nhãn. Nguồn: [bài báo PhoBERT](https://arxiv.org/abs/2003.00744), [repository của tác giả](https://github.com/VinAIResearch/PhoBERT).

Luồng của dự án: câu → tách từ PyVi → tokenizer → token ID/attention mask → encoder → classification head → logits. Khi phục vụ cần softmax để tính xác suất; softmax không bảo đảm đã hiệu chuẩn. Với PyVi, cần đánh giá thực nghiệm sự phù hợp với tiền xử lý checkpoint thay vì giả định mọi bộ tách từ tương đương.

### Cấu hình và mức hoàn thiện

ml/training/phobert.py huấn luyện hai mô hình độc lập, chọn checkpoint theo macro F1 validation mỗi epoch. Config mặc định: max_length=128, train batch=8, evaluation batch=16, learning_rate=2e-5, 5 epoch, weight_decay=0,01. Pipeline mới sử dụng warmup_ratio=0,1 từ config và yêu cầu pin model revision.

Pipeline có load_best_model_at_end và early stopping patience=2. Hai task dùng chung schema metrics. Backend đã có PhoBERT adapter và shared CPU runtime; chọn qua MODEL_BACKEND cùng hai task run paths, không đổi đường dẫn Joblib để phục vụ checkpoint.

## So sánh hai hướng

| Khía cạnh | Baseline | PhoBERT |
| --- | --- | --- |
| Biểu diễn | TF-IDF thưa, n-gram | Biểu diễn theo ngữ cảnh |
| Tài nguyên | Thường nhẹ, thuận tiện CPU | Tốn bộ nhớ và tính toán hơn |
| Khả năng giải thích | Có thể xem trọng số đặc trưng | Cần phương pháp giải thích bổ sung |
| Hạn chế | Khó với ngữ cảnh dài, cách diễn đạt mới | Có thể sai tự tin, nhạy dữ liệu và cấu hình |
| Trạng thái | Có official run và artifact riêng; legacy không dùng nghiệm thu | Có hai checkpoint imported, CPU reload/benchmark và API adapter; xem [trạng thái](../status.md) |

Không mặc định PhoBERT thắng. Chỉ chọn sau khi so sánh trên cùng dữ liệu thật, cùng quy trình đánh giá và phần cứng công bố.

Lệnh thực thi và output được duy trì tại [ML workflow](../../ml/README.md). Các artifact cũ vẫn là kết quả lịch sử từ dữ liệu tổng hợp; code mới không dùng chúng làm benchmark.
