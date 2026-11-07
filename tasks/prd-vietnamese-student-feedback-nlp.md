# PRD: Hệ thống phân loại chủ đề và phân tích cảm xúc phản hồi sinh viên

## 1. Tổng quan

Xây dựng hệ thống NLP xử lý phản hồi tiếng Việt của sinh viên, tự động dự đoán **cảm xúc** và **chủ đề**, sau đó cung cấp kết quả qua API và ứng dụng web. Hệ thống giúp cán bộ/giảng viên nhanh chóng nhận biết phản hồi tích cực, trung tính, tiêu cực và các mảng cần cải thiện thay vì phải đọc, tổng hợp thủ công.

Nguồn dữ liệu chính là [UIT-VSFC trên Hugging Face](https://huggingface.co/datasets/uitnlp/vietnamese_students_feedback): 16.175 câu phản hồi tiếng Việt đã được gán nhãn. Bộ dữ liệu có ba nhãn cảm xúc (`negative`, `neutral`, `positive`) và bốn nhãn chủ đề (`lecturer`, `training_program`, `facility`, `others`), với các tập train/validation/test đã có sẵn.

Phạm vi bao gồm: xây dựng và so sánh baseline với Transformer, triển khai dịch vụ dự đoán, giao diện nhập phản hồi, dashboard tổng quan, và xuất báo cáo CSV/PDF.

## 2. Mục tiêu

- Huấn luyện hai hướng mô hình: baseline truyền thống và Transformer tiếng Việt, trên cùng cách chia dữ liệu để so sánh công bằng.
- Dự đoán đồng thời một nhãn cảm xúc và một nhãn chủ đề cho mỗi phản hồi tiếng Việt.
- Đạt macro F1 tối thiểu 0,80 cho cảm xúc và 0,75 cho chủ đề trên tập test đối với mô hình được chọn để triển khai; công bố cả kết quả không đạt ngưỡng nếu dữ liệu/thí nghiệm cho kết quả khác.
- Cung cấp demo web hoàn chỉnh: nhập phản hồi, xem nhãn và độ tin cậy, theo dõi thống kê, xuất báo cáo.
- Cung cấp API có tài liệu để tích hợp với hệ thống khảo sát khác.

## 3. Người dùng và vai trò

- **Cán bộ khảo thí/quản trị:** xem dashboard, lọc kết quả và xuất báo cáo.
- **Giảng viên:** xem các phản hồi và xu hướng thuộc phạm vi được cấp quyền (trong MVP có thể dùng dữ liệu mẫu, chưa cần phân quyền chi tiết).
- **Người dùng tích hợp:** gọi API để gửi một hoặc nhiều phản hồi và nhận kết quả dự đoán.
- **Nhà nghiên cứu/nhóm phát triển:** tái lập quá trình tiền xử lý, huấn luyện, đánh giá và chọn mô hình.

## 4. User stories

### US-001: Tải và kiểm tra dữ liệu
**Description:** Là nhà nghiên cứu, tôi muốn tải bộ UIT-VSFC và kiểm tra cấu trúc/nhãn để dữ liệu đầu vào dùng cho huấn luyện là nhất quán.

**Acceptance Criteria:**
- [ ] Có script hoặc notebook tải dataset `uitnlp/vietnamese_students_feedback` bằng thư viện `datasets`.
- [ ] Xác nhận ba split `train`, `validation`, `test` được sử dụng, không trộn hoặc làm rò rỉ mẫu giữa các split.
- [ ] Ánh xạ nhãn được lưu rõ ràng: sentiment `0=negative, 1=neutral, 2=positive`; topic `0=lecturer, 1=training_program, 2=facility, 3=others`.
- [ ] Tạo báo cáo số mẫu và phân bố nhãn cho từng split.

### US-002: Tiền xử lý văn bản tiếng Việt
**Description:** Là nhà nghiên cứu, tôi muốn có pipeline tiền xử lý có thể tái lập để dữ liệu phù hợp với từng loại mô hình.

**Acceptance Criteria:**
- [ ] Pipeline xử lý chuỗi rỗng, khoảng trắng thừa và ký tự bất thường mà không thay đổi nhãn.
- [ ] Lưu văn bản gốc và văn bản đã xử lý thành hai trường riêng.
- [ ] Baseline dùng phiên bản văn bản đã chuẩn hóa; Transformer dùng tokenizer của checkpoint đã chọn và không áp dụng tách từ làm mất thông tin ngoài cấu hình tokenizer.
- [ ] Tất cả tham số tiền xử lý được cấu hình được và ghi lại trong kết quả thí nghiệm.

### US-003: Huấn luyện baseline
**Description:** Là nhà nghiên cứu, tôi muốn huấn luyện baseline TF-IDF kết hợp mô hình học máy để có mốc chất lượng minh bạch.

**Acceptance Criteria:**
- [ ] Huấn luyện riêng hai bộ phân loại đa lớp cho cảm xúc và chủ đề, dùng TF-IDF và một thuật toán được cấu hình rõ (ví dụ Linear SVM hoặc Logistic Regression).
- [ ] Tinh chỉnh siêu tham số chỉ trên validation; test chỉ chạy một lần cho cấu hình cuối cùng.
- [ ] Lưu mô hình, vectorizer, cấu hình, seed và metrics theo phiên bản.
- [ ] Xuất accuracy, macro F1, weighted F1, precision/recall/F1 theo từng lớp và confusion matrix cho cả hai tác vụ.

### US-004: Fine-tune Transformer tiếng Việt
**Description:** Là nhà nghiên cứu, tôi muốn fine-tune mô hình Transformer tiếng Việt để so sánh với baseline và chọn mô hình triển khai.

**Acceptance Criteria:**
- [ ] Dùng checkpoint Transformer tiếng Việt được công bố (mặc định PhoBERT hoặc một checkpoint tương đương được ghi rõ).
- [ ] Huấn luyện và đánh giá riêng cho cảm xúc và chủ đề, hoặc kiến trúc đa nhiệm nếu được thực hiện; cách chọn phải được mô tả trong tài liệu.
- [ ] Dùng validation cho early stopping/chọn checkpoint tốt nhất theo macro F1.
- [ ] Lưu checkpoint tốt nhất, tokenizer, cấu hình, seed, log huấn luyện và metrics cùng định dạng với baseline.

### US-005: So sánh và chọn mô hình
**Description:** Là nhà nghiên cứu, tôi muốn bảng so sánh có thể tái lập để chọn mô hình cân bằng chất lượng và chi phí vận hành.

**Acceptance Criteria:**
- [ ] Bảng kết quả so sánh baseline và Transformer trên cùng test split cho từng tác vụ.
- [ ] Bảng gồm macro F1, weighted F1, accuracy, thời gian suy luận trung bình trên CPU và kích thước artifact.
- [ ] Quyết định mô hình triển khai nêu rõ lý do; ưu tiên macro F1, sau đó độ trễ và khả năng chạy trên hạ tầng mục tiêu.
- [ ] Phân tích tối thiểu 10 lỗi dự đoán đại diện (nếu có) và đề xuất hướng cải thiện.

### US-006: API dự đoán
**Description:** Là người dùng tích hợp, tôi muốn gửi phản hồi qua API và nhận nhãn chủ đề/cảm xúc để tự động hóa luồng khảo sát.

**Acceptance Criteria:**
- [ ] Có endpoint `POST /api/v1/predictions` nhận `text` là chuỗi tiếng Việt không rỗng.
- [ ] Phản hồi trả về văn bản gốc, nhãn cảm xúc, nhãn chủ đề, confidence cho từng dự đoán và phiên bản mô hình.
- [ ] Có endpoint batch, giới hạn tối đa 100 phản hồi mỗi yêu cầu và giữ đúng thứ tự đầu vào.
- [ ] Dữ liệu không hợp lệ trả HTTP 422 cùng thông báo lỗi có thể hiểu được; lỗi hệ thống không để lộ stack trace.
- [ ] Xuất tài liệu OpenAPI/Swagger và ví dụ request/response.

### US-007: Nhập và xem dự đoán trên web
**Description:** Là cán bộ khảo thí, tôi muốn nhập phản hồi tiếng Việt trong giao diện để xem ngay kết quả phân loại.

**Acceptance Criteria:**
- [ ] Có ô nhập một phản hồi, nút phân tích và giới hạn ký tự được hiển thị.
- [ ] Khi xử lý xong, trang hiển thị nhãn cảm xúc, nhãn chủ đề, confidence và văn bản gốc.
- [ ] Có trạng thái tải, trạng thái lỗi và hướng dẫn khi nội dung trống.
- [ ] Nhãn cảm xúc không chỉ dựa vào màu sắc; phải có văn bản/biểu tượng dễ hiểu và tương phản đạt mức AA.
- [ ] Verify in browser using dev-browser skill.

### US-008: Dashboard phân tích
**Description:** Là cán bộ khảo thí, tôi muốn xem xu hướng tổng hợp để xác định vấn đề cần ưu tiên.

**Acceptance Criteria:**
- [ ] Dashboard hiển thị tổng số phản hồi và phân bố theo cảm xúc/chủ đề.
- [ ] Có biểu đồ chéo chủ đề × cảm xúc và bảng phản hồi đã phân tích.
- [ ] Có bộ lọc theo cảm xúc, chủ đề và khoảng thời gian nếu dữ liệu đầu vào có timestamp; nếu không có timestamp, UI phải ẩn/vô hiệu bộ lọc này.
- [ ] Bộ lọc cập nhật biểu đồ, số liệu và bảng kết quả nhất quán.
- [ ] Có empty state rõ ràng khi không có dữ liệu phù hợp.
- [ ] Verify in browser using dev-browser skill.

### US-009: Xuất báo cáo
**Description:** Là cán bộ khảo thí, tôi muốn tải báo cáo để chia sẻ kết quả phân tích.

**Acceptance Criteria:**
- [ ] Cho phép xuất CSV của các dòng đang được lọc với văn bản, nhãn, confidence và thời điểm phân tích.
- [ ] Cho phép xuất PDF gồm phạm vi/bộ lọc báo cáo, số liệu tổng quan và biểu đồ phân bố.
- [ ] Tên tệp bao gồm ngày giờ xuất theo múi giờ `Asia/Ho_Chi_Minh`.
- [ ] Tệp xuất giữ nguyên tiếng Việt có dấu khi mở bằng phần mềm phổ biến.
- [ ] Verify in browser using dev-browser skill.

## 5. Yêu cầu chức năng

- **FR-1:** Hệ thống phải tải và dùng các split chuẩn của `uitnlp/vietnamese_students_feedback` cho huấn luyện, validation và test.
- **FR-2:** Hệ thống phải dự đoán đúng không gian nhãn gồm 3 nhãn cảm xúc và 4 nhãn chủ đề đã định nghĩa.
- **FR-3:** Hệ thống phải có pipeline tái lập được từ tải dữ liệu đến đánh giá, cố định random seed và lưu cấu hình chạy.
- **FR-4:** Hệ thống phải huấn luyện, đánh giá và lưu artifacts của một baseline TF-IDF + ML và một Transformer tiếng Việt.
- **FR-5:** Hệ thống phải sinh báo cáo đánh giá đầy đủ cho từng mô hình và từng tác vụ trên test split.
- **FR-6:** Hệ thống phải cung cấp API dự đoán đơn lẻ và batch với schema được kiểm tra.
- **FR-7:** Ứng dụng web phải cho phép nhập phản hồi, gọi API và trình bày kết quả dự đoán rõ ràng bằng tiếng Việt.
- **FR-8:** Dashboard phải tổng hợp các phản hồi đã được phân tích, hỗ trợ lọc theo nhãn và hiển thị số liệu/biểu đồ đồng bộ.
- **FR-9:** Hệ thống phải cho phép tải CSV và PDF theo tập dữ liệu/bộ lọc hiện tại.
- **FR-10:** Mọi kết quả dự đoán được lưu cùng `model_version`, thời điểm xử lý và confidence để truy vết.

## 6. Yêu cầu phi chức năng

- **NFR-1 — Hiệu năng:** API đơn lẻ phải trả kết quả p95 dưới 2 giây trên hạ tầng demo đã công bố; đo riêng thời gian nạp mô hình và suy luận.
- **NFR-2 — Khả dụng:** Giao diện đáp ứng tốt trên màn hình desktop từ 1280 px và mobile từ 360 px.
- **NFR-3 — Khả năng tái lập:** Mỗi thí nghiệm phải ghi seed, phiên bản dataset/model/thư viện, cấu hình và commit mã nguồn nếu có Git.
- **NFR-4 — Chất lượng:** Mã nguồn phải chạy lint/typecheck và có test tự động cho ánh xạ nhãn, validation API và một luồng dự đoán mẫu.
- **NFR-5 — Quyền riêng tư:** Không lưu thông tin định danh cá nhân không cần thiết; tài liệu nêu rõ dữ liệu demo không được xem như đánh giá thực tế của cá nhân.
- **NFR-6 — Khả năng truy cập:** UI đạt tương phản WCAG AA cho thành phần văn bản/chức năng chính và có thể thao tác bằng bàn phím.

## 7. Thiết kế và trải nghiệm

- Ngôn ngữ giao diện là tiếng Việt.
- Màn hình chính ưu tiên hai luồng: **Phân tích phản hồi** và **Dashboard**.
- Kết quả dùng badge có chữ rõ ràng: tiêu cực/trung tính/tích cực và giảng viên/chương trình đào tạo/cơ sở vật chất/khác.
- Dashboard dùng biểu đồ cột hoặc donut cho phân bố, biểu đồ cột chồng cho chủ đề × cảm xúc; mọi biểu đồ phải có số liệu thay thế dạng bảng hoặc tooltip.
- Confidence là xác suất dự đoán, không được trình bày như mức độ hài lòng hay sự thật tuyệt đối.

## 8. Cân nhắc kỹ thuật

- Gợi ý kiến trúc: frontend web → REST API → dịch vụ suy luận → kho lưu kết quả; pipeline huấn luyện tách khỏi ứng dụng chạy production.
- Stack cụ thể sẽ được nhóm chọn sau; yêu cầu tối thiểu là Python, `datasets`, `scikit-learn`, một thư viện Transformer tương thích checkpoint tiếng Việt, và framework API có OpenAPI.

### Mô hình baseline: TF-IDF + Linear SVM

Baseline sử dụng `TfidfVectorizer` để chuyển phản hồi tiếng Việt thành vector thưa, sau đó dùng `LinearSVC` (Linear Support Vector Machine) làm bộ phân loại đa lớp. Cấu hình khởi đầu là word n-gram từ 1 đến 2 từ; nhóm có thể thử thêm character n-gram từ 3 đến 5 ký tự nếu validation cho thấy cải thiện. Các tham số như `min_df`, `max_df`, số lượng đặc trưng và `C` của SVM chỉ được chọn dựa trên validation, không dùng test set để tối ưu.

Huấn luyện hai pipeline độc lập: pipeline thứ nhất dự đoán cảm xúc (`negative`, `neutral`, `positive`), pipeline thứ hai dự đoán chủ đề (`lecturer`, `training_program`, `facility`, `others`). Mô hình này nhẹ, suy luận nhanh trên CPU và dễ tái lập; nó là mốc so sánh bắt buộc trước khi chọn mô hình phức tạp hơn. Do `LinearSVC` không tạo xác suất mặc định, confidence hiển thị cho API/UI phải được hiệu chuẩn bằng `CalibratedClassifierCV` hoặc chuyển sang `LogisticRegression` nếu cần xác suất đáng tin cậy.

### Mô hình Transformer tiếng Việt: PhoBERT-base

Mô hình chính để fine-tune là `vinai/phobert-base`, một Transformer được tiền huấn luyện cho tiếng Việt. Văn bản đầu vào được mã hóa bằng tokenizer đi kèm PhoBERT; không dùng TF-IDF trong pipeline này. Nhóm phải ghi rõ phiên bản checkpoint, tokenizer, độ dài chuỗi tối đa, batch size, learning rate, số epoch và random seed trong mỗi lần chạy.

Tương tự baseline, phiên bản MVP fine-tune hai mô hình phân loại độc lập: một mô hình có đầu ra 3 lớp cho cảm xúc và một mô hình có đầu ra 4 lớp cho chủ đề. Checkpoint được chọn theo macro F1 trên validation; dùng early stopping để hạn chế overfitting. PhoBERT được kỳ vọng hiểu ngữ cảnh, phủ định và cách diễn đạt đa dạng tốt hơn baseline, nhưng chi phí huấn luyện/suy luận cao hơn và nên dùng GPU khi huấn luyện. Bản demo vẫn phải benchmark và hỗ trợ suy luận CPU nếu môi trường triển khai không có GPU.

### Nguyên tắc so sánh và chọn mô hình

Hai hướng mô hình sử dụng cùng train/validation/test split và cùng cách ánh xạ nhãn. So sánh theo macro F1 là chính, kèm accuracy, weighted F1, chất lượng theo từng lớp, độ trễ CPU, kích thước artifact và khả năng vận hành. Chọn PhoBERT khi cải thiện chất lượng có ý nghĩa và vẫn đạt yêu cầu độ trễ; chọn baseline khi chất lượng tương đương nhưng đơn giản, nhanh hoặc tiết kiệm tài nguyên hơn.

- Chỉ dùng dữ liệu theo điều khoản cho phép. Dataset card hiện nêu giấy phép là `unknown`; cần xác minh điều kiện sử dụng với nguồn/công bố gốc trước khi thương mại hóa hoặc dùng dữ liệu ngoài phạm vi học thuật.
- API cần versioning ngay từ đầu (`/api/v1`) để hỗ trợ thay mô hình mà không phá vỡ client.

## 9. Ngoài phạm vi

- Thu thập phản hồi trực tiếp từ hệ thống khảo sát thật hoặc tích hợp SSO/LMS trong phiên bản đầu.
- Phân tích đa ngôn ngữ ngoài tiếng Việt.
- Phân loại đa nhãn, phát hiện mỉa mai, trích xuất khía cạnh/ý định, tóm tắt sinh ngôn ngữ hoặc chatbot tư vấn.
- Chấm điểm hay xếp hạng cá nhân giảng viên/sinh viên, đưa ra quyết định kỷ luật hoặc tự động can thiệp dựa trên dự đoán.
- Phân quyền chi tiết theo khoa/lớp, audit log doanh nghiệp và triển khai high-availability.
- Huấn luyện lại tự động/continuous learning từ phản hồi người dùng.

## 10. Chỉ số thành công

| Nhóm | Chỉ số | Mục tiêu xác nhận |
|---|---|---|
| Chất lượng mô hình | Macro F1 trên test | Mục tiêu khởi đầu: ≥ 0,80 cảm xúc; ≥ 0,75 chủ đề; xác nhận/điều chỉnh sau benchmark đầu tiên |
| So sánh | Báo cáo hai mô hình | Có đủ metric theo lớp, confusion matrix, độ trễ, artifact size |
| API | Tỷ lệ request mẫu hợp lệ thành công | 100% trong bộ smoke test |
| Hiệu năng | p95 dự đoán đơn lẻ | < 2 giây trên môi trường demo công bố |
| Demo | Luồng nhập → dự đoán → dashboard → xuất báo cáo | Hoàn thành trong kiểm thử nghiệm thu |
| Khả dụng | Mức hoàn thành tác vụ của người dùng thử | ≥ 80% với kịch bản phân tích và xuất báo cáo |

## 11. Rủi ro và giảm thiểu

- **Mất cân bằng nhãn/nhãn chủ đề mơ hồ:** báo cáo phân bố, macro F1 theo lớp, confusion matrix; cân nhắc class weighting sau khi kiểm tra validation.
- **Dữ liệu không đại diện cho trường hiện tại:** hiển thị giới hạn dữ liệu và chỉ xem mô hình là công cụ hỗ trợ; lập kế hoạch đánh giá trên dữ liệu mới đã được phê duyệt.
- **Rò rỉ dữ liệu:** khóa split chuẩn và dùng validation, không dùng test để tối ưu siêu tham số.
- **Chi phí/độ trễ Transformer:** benchmark CPU, giữ baseline là phương án thay thế và tối ưu kích thước batch/sequence length.
- **Giấy phép chưa rõ:** xác minh trước mọi phát hành hoặc sử dụng thương mại.

## 12. Quyết định phạm vi và giả định đã chốt

### 12.1. Sở hữu và vận hành dữ liệu

Trong phạm vi đồ án, nhóm phát triển và vận hành hệ thống thử nghiệm, sử dụng bộ dữ liệu công khai UIT-VSFC. Nếu triển khai thực tế tại trường, đơn vị đào tạo hoặc đơn vị được nhà trường ủy quyền sẽ chịu trách nhiệm quản lý dữ liệu phản hồi mới. Dữ liệu nội bộ chỉ được nhập và sử dụng khi có sự cho phép của nhà trường.

### 12.2. Đăng nhập và phân quyền

Phiên bản đầu có thể triển khai đăng nhập cơ bản cho quản trị viên và người xem dashboard khi cần bảo vệ dữ liệu demo. Phân quyền chi tiết theo khoa, môn học hoặc giảng viên không thuộc MVP; đây là hạng mục mở rộng, được quyết định theo nhu cầu thực tế và quyền truy cập dữ liệu của đơn vị vận hành.

### 12.3. Nguồn dữ liệu dashboard

Dashboard phiên bản đầu dùng UIT-VSFC để huấn luyện, đánh giá mô hình và minh họa thống kê. Hệ thống có thể hỗ trợ nhập dữ liệu CSV để thử nghiệm. Dữ liệu nội bộ chỉ được dùng sau khi được phê duyệt và đã áp dụng biện pháp xử lý phù hợp với thông tin cá nhân.

### 12.4. Hạ tầng triển khai

Bản demo phải chạy được trên CPU để bảo đảm tính khả thi và dễ triển khai. GPU là tài nguyên tùy chọn, được dùng cho huấn luyện hoặc thử nghiệm Transformer khi có sẵn. Trước khi chốt yêu cầu phần cứng chính thức, nhóm phải đo độ trễ suy luận thực tế của cả baseline và PhoBERT trên CPU.

### 12.5. Xác nhận mục tiêu F1

Ngưỡng macro F1 tại phần chỉ số thành công là mục tiêu ban đầu, được đặt theo nghiên cứu liên quan và năng lực dự kiến của mô hình, không phải cam kết hiệu năng chưa kiểm chứng. Sau benchmark đầu tiên, nhóm phải xem xét phân bố nhãn, macro F1 và F1 theo từng lớp trên validation/test; sau đó ghi nhận mục tiêu cuối cùng cùng lý do điều chỉnh trong báo cáo thí nghiệm.

