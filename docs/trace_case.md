# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Case đã phân tích — C-002@11

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`; đối chứng `fixed C-002@11` |
| Triệu chứng | Lab 8 grader fail: trạng thái `resolved` thay vì `denied`; ledger ghi 20.000 VND, nhãn kỳ vọng 0 VND. |
| Bước sai đầu tiên | Event 3 `model_override`: agent ghi nhận `delay_days: 5` từ ticket, trong khi dữ kiện DB không cho phép áp dụng entitlement. |
| Vì sao là bước đầu tiên | Event 1 giao đúng phạm vi principal; event 2 đọc order từ investigator. Event 3 là lần đầu agent thay dữ kiện bằng lời khai; quote ở event 4 và refund sau đó là hệ quả. |
| Failure mode | FM-03 `ticket_trust` |
| Đối chứng | Với `fixed`, event 3 `quote` trả `amount_vnd: 0`, không có `model_override`, và ledger vẫn 0. |
| Regression test | `test_seeded_regression_c002_detects_first_wrong_step` trong `tests/test_lab9_trace_case.py`; xác nhận variant sai và `fixed` đối chứng. |
| Chưa chắc chắn | Trace chứng minh override và hậu quả trên ca này; không chứng minh mọi claim có cùng dạng sẽ lỗi. |

## Mẫu điền (mỗi nhóm 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `<shape> <claim>@<seed>`, run ID trong report |
| Triệu chứng | Grader nào fail; reply nói gì so với ledger ghi gì |
| Bước sai đầu tiên | Số thứ tự event + kind + trích payload (≤1 dòng) |
| Vì sao là bước *đầu tiên* | Các bước trước đó đúng ra sao (dẫn số event) |
| Failure mode | Mã FM-xx trong `docs/failure_taxonomy.md` |
| Đối chứng | Cùng claim@seed trên shape `fixed`: bước đó khác thế nào |
| Regression test | Tên test + grader/assert nào bắt được; đã thấy fail trên variant lỗi và pass trên `fixed` chưa |
| Chưa chắc chắn | Điều trace không chứng minh được |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
