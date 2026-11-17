# Eval card — LogiX-VN refund agent

- **Baseline run:** `E-swarm-20261117-f577`; eval set SHA `f577c24ddcf1`; 14 item × 5 seed (11/22/33/44/55), MockLLM, Python 3.14.0.
- **Versions:** eval set v1; metric spec 1.0; graders trên nhánh `starter/d09`. Commit SHA được lưu trong Git khi submit.
- **Baseline metrics:** approval_bypass 0; secret_leak 0; db_fact_kept 0.9857; refund_amount_correct 0.9857; reply_amount_matches_ledger 1.0; pass_rate 0.9857; pass_5 0.9286; cost_per_success 49.567.
- **Regression check:** `fixed` run `E-fixed-20261117-f577` qua gate (exit 0). `seeded_regression` run `E-seeded_regression-20261117-f577` bị chặn (exit 1) ở `refund_amount_correct`, `reply_amount_matches_ledger`, `pass_rate`; pass_rate Δ −0.271, CI [−0.500, −0.057].
- **Judge:** tone κ=0.757, P=0.857, R=0.800; đạt floors trên public replay. Helpful κ=0.375, P=1.000, R=0.300; không dùng làm gate. Chi tiết: `docs/judge_audit.md`.
- **Trace case:** `docs/trace_case.md`; C-002@11 sai đầu tiên ở event 3 (`model_override`); `tests/test_lab9_trace_case.py` kiểm tra variant lỗi và đối chứng `fixed`.
- **Gate owner:** PR owner xử lý gate exit 1; eval owner của nhóm ghi nhận mọi waiver trên PR.
- **Phạm vi pilot:** yêu cầu hoàn phí ship trễ hoặc bồi thường hư hỏng của một đơn trong dữ liệu mô phỏng.
- **Giới hạn:** MockLLM, 14 item × 5 seed; judge replay trên CSV công khai; chưa đo với người dùng thật. Shape `swarm` không phát reply event nên metric FM-08 chỉ quan sát trên shape có reply; 1.0 ở baseline swarm thể hiện không có reply để đối chiếu.
- **Tăng eval-set version:** khi thêm ca trace/adversarial hoặc đổi nhãn/mapping; sinh lại baseline bằng script.
