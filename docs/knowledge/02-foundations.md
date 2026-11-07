# 02. Kiến thức nền

[Chỉ mục](README.md) · [Tiếp: Mô hình](03-models.md)

## Học có giám sát

Một mẫu gồm văn bản x và nhãn chuẩn y. Huấn luyện tìm tham số để dự đoán nhãn từ văn bản; suy luận áp dụng tham số đã học lên văn bản mới. Tham số như trọng số SVM được học từ train; siêu tham số như C, learning rate và số epoch được lựa chọn qua thí nghiệm.

Overfitting xảy ra khi mô hình học quá sát dữ liệu huấn luyện và tổng quát hóa kém. Underfitting là khi biểu diễn hoặc mô hình chưa học đủ tín hiệu. Điểm train cao không đủ để đánh giá; phải so với validation độc lập và phân tích sai số.

## Đặc điểm tiếng Việt

Khoảng trắng thường phân cách âm tiết, không luôn phân cách từ. “sinh viên” gồm hai âm tiết nhưng có thể được xử lý như một đơn vị từ. Dấu thanh, chữ đ, Unicode tổ hợp và viết tắt như gv/ko làm tiền xử lý quan trọng. Ngữ cảnh phủ định như “không tốt” cần được giữ lại; xóa “không” có thể đảo nghĩa.

Phản hồi còn có mỉa mai, lỗi chính tả và cách nói phụ thuộc ngữ cảnh. Ví dụ minh họa “hay quá, lại mất wifi” khó giải thích bằng quy tắc từ khóa đơn giản.

## Chuẩn hóa, tách từ và tokenize

| Bước | Ý nghĩa | Ví dụ minh họa |
| --- | --- | --- |
| Chuẩn hóa Unicode NFC | Thống nhất cách biểu diễn ký tự tương đương | Dấu tổ hợp thành dạng chuẩn |
| Chuẩn hóa khoảng trắng | Bỏ khoảng trắng đầu/cuối, gộp khoảng trắng liên tiếp | “thầy   dạy” → “thầy dạy” |
| Tách từ | Nhận diện đơn vị từ tiếng Việt | “sinh viên” → “sinh_viên” |
| Tokenize subword | Chuyển văn bản thành các mảnh từ và token ID | Thực hiện bởi tokenizer checkpoint |

backend/app/preprocessing.py chuẩn hóa NFC và khoảng trắng, giữ dấu, chữ hoa/thường và dấu câu. Luồng hiện tại lưu cả raw_text và text đã chuẩn hóa. Legacy raw_text chỉ được backfill từ text đang có, không khôi phục được nguyên bản đã mất.

Baseline hiện dùng word tokenization mặc định của TfidfVectorizer; không gọi bộ tách từ tiếng Việt. Pipeline PhoBERT mới gọi normalize_text và dùng PyVi trước tokenizer, nhất quán với bước chuẩn hóa snapshot.

## Biểu diễn văn bản

Bag-of-words biểu diễn văn bản bằng số lần xuất hiện token và bỏ phần lớn trật tự. N-gram giữ các cụm liên tiếp: unigram “không”, “tốt”; bigram “không tốt”. TF-IDF giảm ảnh hưởng của token phổ biến trên nhiều tài liệu và tạo vector thưa.

Embedding là vector đặc, thường có số chiều cố định. Với Transformer, biểu diễn một token phụ thuộc các token khác trong câu. Biểu diễn theo ngữ cảnh không có nghĩa mô hình luôn hiểu đúng ngôn ngữ hay kiểm chứng được sự thật.

## Thuật ngữ thực hành

| Thuật ngữ | Giải thích |
| --- | --- |
| Corpus | Tập văn bản dùng nghiên cứu |
| Vocabulary | Tập token đã được vectorizer học |
| Batch | Nhóm mẫu xử lý trong một bước |
| Epoch | Một lượt đi qua dữ liệu train |
| Loss | Đại lượng tối ưu trong huấn luyện |
| Checkpoint | Trạng thái mô hình lưu tại một thời điểm |
| Artifact | Gói mô hình và dữ liệu cần để phục vụ suy luận |
| Seed | Giá trị khởi tạo bộ sinh số ngẫu nhiên |
| Distribution shift | Dữ liệu vận hành khác phân bố huấn luyện |

Seed hỗ trợ tái lập nhưng không bảo đảm mọi phép toán GPU cho kết quả bit giống nhau. Cần lưu thêm phiên bản thư viện, dữ liệu và phần cứng.
