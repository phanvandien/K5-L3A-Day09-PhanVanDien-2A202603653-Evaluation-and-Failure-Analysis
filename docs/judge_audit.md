# Judge audit — public replay

Chạy: `python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5`. `FAIL` là lớp dương; nhãn người là chuẩn tham chiếu cho tập replay công khai.

| Tiêu chí | n | κ | Precision | Recall | Đạt floors? | Quyết định |
|---|---:|---:|---:|---:|---|---|
| tone | 100 | 0.757 | 0.857 | 0.800 | Có | Có thể dùng cho đánh giá tone có kiểm soát; tiếp tục review sai khác. |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không | Không dùng làm gate; bỏ sót 21/30 failure. |

## 5 bất đồng của tone

| Case | Judge | Người | Ai đúng / điều chỉnh rubric |
|---|---|---|---|
| H-008 | PASS | FAIL | Người đúng: “em … nha” suồng sã; thêm ví dụ xưng hô suồng sã. |
| H-017 | PASS | FAIL | Người đúng: cách gọi “bạn ơi” và lời khẳng định thân mật không hợp ngữ cảnh CSKH; thêm ví dụ tone quá thân mật. |
| H-029 | PASS | FAIL | Người đúng: “không cần nhắn thêm” cụt và gạt nhu cầu hỗ trợ; thêm ví dụ câu thiếu tôn trọng. |
| H-042 | FAIL | PASS | Người đúng: lời lịch sự, thông tin rõ; thêm ví dụ câu ngắn gọn vẫn đạt tone. |
| H-051 | FAIL | PASS | Người đúng: từ “refund” không tự nó làm câu thô lỗ; tách từ vay mượn khỏi thái độ. |

## 5 bất đồng của helpful

| Case | Judge | Người | Ai đúng / điều chỉnh rubric |
|---|---|---|---|
| HL-015 | PASS | FAIL | Người đúng: 55.000đ sai, ledger ghi 40.000đ; chuyển kiểm tra tiền sang code grader. |
| HL-016 | PASS | FAIL | Người đúng: reply ghi 55.000đ thay vì 35.000đ; rubric phải kiểm tra tính đúng trước độ trôi chảy. |
| HL-020 | PASS | FAIL | Người đúng: reply ghi 90.000đ, ledger 120.000đ; chỉ code mới có dữ kiện đối chiếu. |
| HL-028 | PASS | FAIL | Người đúng: reply ghi 50.000đ thay vì 35.000đ; thêm ví dụ sai tiền dù câu lịch sự. |
| HL-035 | PASS | FAIL | Người đúng: reply ghi 50.000đ thay vì 35.000đ; rubric nhấn mạnh tính đúng và hữu ích là hai chiều riêng. |

Tone đạt floors κ≥0.6, P≥0.8, R≥0.7 trên replay công khai; chưa có held-out nên chưa dùng làm cổng release. Helpful không đạt κ/recall và không dùng làm gate. Tiền và approval luôn chấm bằng code.
