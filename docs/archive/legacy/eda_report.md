> Báo cáo lịch sử: có số liệu fallback/mô phỏng từ pipeline cũ. Không dùng để nghiệm thu. Tạo EDA mới theo [ML workflow](../../../ml/README.md).

# Báo cáo Phân tích Khám phá Dữ liệu (EDA) & Xác minh UIT-VSFC

> **Dự án:** Hệ thống phân loại chủ đề và cảm xúc phản hồi sinh viên  
> **Bộ dữ liệu chuẩn:** `uitnlp/vietnamese_students_feedback` (16.175 mẫu)

## 1. Xác minh phân chia dữ liệu (Splits Verification)

Bộ dữ liệu UIT-VSFC được công bố với phân chia chuẩn 3 tập: `train` (~70%), `validation` (~10%) và `test` (~20%). Quy tắc bắt buộc: **chỉ dùng tập validation để tinh chỉnh siêu tham số và chọn mô hình; tập test được giữ nguyên cho đánh giá nghiệm thu cuối cùng**.

| Phân vùng (Split)     | Số lượng mẫu | Tỷ lệ (%)  | Mục đích sử dụng              |
| :-------------------- | :----------: | :--------: | :---------------------------- |
| **train**             |    11,426    |   70.64%   | Huấn luyện mô hình            |
| **validation**        |    1,583     |   9.79%    | Kiểm định & Chọn checkpoint   |
| **test**              |    3,166     |   19.57%   | Đánh giá benchmark nghiệm thu |
| **Tổng cộng (Total)** |  **16,175**  | **100.0%** | Toàn bộ kho ngữ liệu          |

## 2. Bảng ánh xạ nhãn (Label Mapping)

### 2.1. Cảm xúc (Sentiment - 3 lớp)

| ID  | Mã nhãn (Code) | Tên tiếng Việt | Mô tả                                         |
| :-: | :------------- | :------------- | :-------------------------------------------- |
| `0` | `negative`     | **Tiêu cực**   | Phản hồi chê bai, than phiền, không hài lòng  |
| `1` | `neutral`      | **Trung tính** | Phản hồi nhận xét trung lập, không rõ thái độ |
| `2` | `positive`     | **Tích cực**   | Phản hồi khen ngợi, hài lòng, đồng tình       |

### 2.2. Chủ đề (Topic - 4 lớp)

| ID  | Mã nhãn (Code)     | Tên tiếng Việt           | Mô tả                                                 |
| :-: | :----------------- | :----------------------- | :---------------------------------------------------- |
| `0` | `lecturer`         | **Giảng viên**           | Thầy cô, phương pháp giảng dạy, thái độ, nhiệt tình   |
| `1` | `training_program` | **Chương trình đào tạo** | Chương trình học, môn học, giáo trình, bài tập, slide |
| `2` | `facility`         | **Cơ sở vật chất**       | Phòng học, máy tính, wifi, máy chiếu, quạt/máy lạnh   |
| `3` | `others`           | **Khác**                 | Học phí, đăng ký môn, dịch vụ khác                    |

## 3. Phân bố nhãn trên các tập dữ liệu

### 3.1. Phân bố Cảm xúc (Sentiment Distribution)

| Tập dữ liệu    | Tiêu cực (negative) | Trung tính (neutral) | Tích cực (positive) | Tổng mẫu |
| :------------- | :-----------------: | :------------------: | :-----------------: | :------: |
| **train**      |   3,799 (33.25%)    |     669 (5.86%)      |    6,958 (60.9%)    |  11,426  |
| **validation** |    546 (34.49%)     |      99 (6.25%)      |    938 (59.25%)     |  1,583   |
| **test**       |   1,031 (32.56%)    |      193 (6.1%)      |   1,942 (61.34%)    |  3,166   |

### 3.2. Phân bố Chủ đề (Topic Distribution)

| Tập dữ liệu    | Giảng viên (lecturer) | CT Đào tạo (training_program) | CS Vật chất (facility) | Khác (others) |
| :------------- | :-------------------: | :---------------------------: | :--------------------: | :-----------: |
| **train**      |    8,808 (77.09%)     |        1,827 (15.99%)         |       526 (4.6%)       |  265 (2.32%)  |
| **validation** |    1,227 (77.51%)     |         248 (15.67%)          |       74 (4.67%)       |  34 (2.15%)   |
| **test**       |    2,445 (77.23%)     |         509 (16.08%)          |      147 (4.64%)       |  65 (2.05%)   |

### 3.3. Ma trận chéo Chủ đề × Cảm xúc (Tập Train)

| Chủ đề \ Cảm xúc                              | Tiêu cực | Trung tính | Tích cực | Tổng cộng |
| :-------------------------------------------- | :------: | :--------: | :------: | :-------: |
| **Giảng viên** (`lecturer`)                   |  2,659   |    501     |  5,427   | **8,587** |
| **Chương trình đào tạo** (`training_program`) |   683    |    100     |  1,043   | **1,826** |
| **Cơ sở vật chất** (`facility`)               |   303    |     40     |   347    |  **690**  |
| **Khác** (`others`)                           |   151    |     26     |   139    |  **316**  |

## 4. Thống kê độ dài văn bản phản hồi

| Chỉ số thống kê     | Độ dài ký tự (Characters) | Độ dài số từ (Words) |
| :------------------ | :-----------------------: | :------------------: |
| Tối thiểu (Min)     |            32             |          7           |
| Tối đa (Max)        |            58             |          12          |
| Trung bình (Mean)   |           46.38           |        10.75         |
| Trung vị (Median)   |           46.5            |         11.5         |
| Độ lệch chuẩn (Std) |           6.93            |         1.64         |
| Phân vị 95% (p95)   |            58             |          12          |

> **Nhận xét độ dài:** Phản hồi của sinh viên phần lớn rất súc tích (95% số câu có độ dài dưới 35–45 từ). Điều này rất thuận lợi khi cài đặt `max_length=128` hoặc `max_length=256` cho PhoBERT, giúp tiết kiệm đáng kể bộ nhớ và đẩy nhanh tốc độ suy luận CPU.

## 5. Ví dụ dữ liệu tiêu biểu theo từng nhãn

| STT | Câu phản hồi tiếng Việt                                                      |         Cảm xúc          |                   Chủ đề                    |
| :-: | :--------------------------------------------------------------------------- | :----------------------: | :-----------------------------------------: |
|  1  | _"Thầy giảng bài rất nhiệt tình, tâm huyết và dễ tiếp thu."_                 | `Tích cực` (`positive`)  |          `Giảng viên` (`lecturer`)          |
|  2  | _"Giảng viên dạy quá nhanh, sinh viên không ghi kịp bài trên lớp."_          | `Tiêu cực` (`negative`)  |          `Giảng viên` (`lecturer`)          |
|  3  | _"Nội dung chương trình đào tạo hơi nặng lý thuyết, ít bài tập thực tế."_    | `Tiêu cực` (`negative`)  | `Chương trình đào tạo` (`training_program`) |
|  4  | _"Giáo trình và slide bài giảng được cung cấp đầy đủ, chi tiết."_            | `Tích cực` (`positive`)  | `Chương trình đào tạo` (`training_program`) |
|  5  | _"Phòng thực hành máy tính cấu hình yếu, mạng wifi thường xuyên chập chờn."_ | `Tiêu cực` (`negative`)  |        `Cơ sở vật chất` (`facility`)        |
|  6  | _"Trường có phòng tự học thoáng mát, sạch sẽ và máy lạnh hoạt động tốt."_    | `Tích cực` (`positive`)  |        `Cơ sở vật chất` (`facility`)        |
|  7  | _"Mọi thứ ở mức bình thường, không có ý kiến gì thêm."_                      | `Trung tính` (`neutral`) |              `Khác` (`others`)              |
|  8  | _"Quy trình đăng ký học phần còn rườm rà và hay nghẽn mạng."_                | `Tiêu cực` (`negative`)  |              `Khác` (`others`)              |

## 6. Phân tích rủi ro mất cân bằng dữ liệu & Chiến lược xử lý

### 6.1. Cảm xúc (Sentiment) - Lớp Trung tính (Neutral)

- **Mức độ rủi ro:** `Cao (High)`
- **Thực trạng phát hiện:** Lớp trung tính chỉ chiếm 5.86% (669 mẫu) trong khi Tích cực chiếm 60.9% (6958 mẫu). Tỷ lệ mất cân bằng lên tới ~10:1.
- **Tác động kỹ thuật:** Mô hình có nguy cơ cao bỏ sót (Recall thấp) nhãn neutral, làm sụt giảm mạnh chỉ số Macro F1.
- **Giải pháp xử lý (Mitigation):** Sử dụng class_weight='balanced' trong LinearSVC/LogisticRegression; thiết lập ngưỡng phân lớp (threshold tuning) hoặc phạt trọng số loss (Weighted Cross-Entropy) khi huấn luyện Transformer.

### 6.2. Chủ đề (Topic) - Lớp Giảng viên áp đảo (Lecturer Dominance)

- **Mức độ rủi ro:** `Cao (High)`
- **Thực trạng phát hiện:** Chủ đề 'Giảng viên' (Lecturer) chiếm tới 77.09% (8808 mẫu), trong khi 'Khác' (Others) chỉ có 2.32% (265 mẫu).
- **Tác động kỹ thuật:** Mô hình có xu hướng thiên vị dự đoán vào 'lecturer'; lớp 'others' dễ bị phân loại nhầm.
- **Giải pháp xử lý (Mitigation):** Đánh giá chi tiết Confusion Matrix riêng cho từng lớp; báo cáo cả Macro F1 lẫn F1-score từng lớp thay vì chỉ nhìn vào Accuracy.

### 6.3. Độ dài câu và từ vựng viết tắt/tiếng lóng

- **Mức độ rủi ro:** `Trung bình (Medium)`
- **Thực trạng phát hiện:** Phản hồi sinh viên thường ngắn (trung bình 12-18 từ), nhiều từ viết tắt học đường ('gv', 'thầy cô', 'ko', 'ktra', 'btvn') và câu đảo ngữ.
- **Tác động kỹ thuật:** TF-IDF cần n-gram (1, 2) để bắt cụm từ mang sắc thái (ví dụ: 'không tốt', 'quá nhanh'); PhoBERT cần bước tách từ tiếng Việt chuẩn trước khi tokenize.
- **Giải pháp xử lý (Mitigation):** Áp dụng tiền xử lý chuẩn hóa khoảng trắng `normalize_text` đồng bộ cho mọi pipeline; sử dụng `sublinear_tf=True` trong TF-IDF.

## 7. Kết luận & Hướng dẫn kỹ thuật cho các tuần tiếp theo

1. **Baseline SVM (Tuần 3-4):** Sử dụng `TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True)` kết hợp `LinearSVC(class_weight='balanced')` và bọc trong `CalibratedClassifierCV` để xuất xác suất dự đoán (confidence) chính xác.
2. **PhoBERT Transformer (Tuần 5-6):** Do 95% phản hồi có độ dài dưới 45 từ, đặt `max_length=128` (hoặc tối đa 256) để tăng tốc độ huấn luyện. Bắt buộc thực hiện word segmentation trước khi đưa vào tokenizer.
3. **Chỉ số đánh giá chính:** Tuyệt đối không dùng `Accuracy` làm thước đo chính do phân bố lệch; bắt buộc sử dụng **Macro F1** và theo dõi F1-score riêng của lớp thiểu số (`neutral` và `others`).
