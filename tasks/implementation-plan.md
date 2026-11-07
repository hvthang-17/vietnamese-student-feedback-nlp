# Kế hoạch thực hiện

Trạng thái từng giai đoạn, evidence và việc tiếp theo được quản lý duy nhất tại [docs/status.md](../docs/status.md). Không duy trì bảng tiến độ thứ hai ở đây.

## Thứ tự và điều kiện chuyển bước

1. Yêu cầu và protocol → kiến trúc/môi trường → dữ liệu/EDA. Có PRD, contract, snapshot và preprocessing kiểm chứng được.
2. Baseline → PhoBERT → đánh giá/chọn model. Chọn bằng validation, báo cáo test trung thực, so chi phí cùng scope. Baseline dưới target không cản nghiên cứu PhoBERT.
3. API/DB → UI/báo cáo → E2E/vận hành/bàn giao. Code có thể làm song song sau khi chốt contract; nghiệm thu tích hợp phải dùng model được chọn.

Mỗi bước: xác định đầu vào/đầu ra → thực hiện → lưu evidence → review gate. Xem [PRD](prd-vietnamese-student-feedback-nlp.md), [protocol](experiment-protocol.md), [quy trình NLP](../docs/workflows/nlp-processing-workflow.md). Chưa chốt lịch/nhân lực nên không tự gán deadline.
