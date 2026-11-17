# Demo Lab 9 — Kịch bản trình bày

## Mục tiêu

Giải thích trong 3–5 phút cách eval so sánh agent, phát hiện hồi quy, tìm nguyên nhân từ trace và kiểm tra độ tin cậy của judge.

## Chuẩn bị

1. Mở `demo/index.html` bằng Chrome/Edge. Trang chạy offline, không cần API key hay cài thêm package.
2. Phóng to 100% hoặc bật toàn màn hình; dùng trình duyệt ngang màn hình.
3. Để mở thêm `docs/trace_case.md` nếu người xem muốn đọc chi tiết case.

## Kịch bản nói 3 phút

### 0:00–0:30 — Vấn đề

> “Một bản agent chạy được chưa có nghĩa là bản mới tốt hơn. Lab 9 chạy cùng bộ ca và seed trên từng phiên bản, đo theo metric, rồi chặn merge nếu bản mới hồi quy.”

Chỉ vào số liệu trên đầu trang: 14 item × 5 seed, MockLLM và eval SHA. Nói rõ đây là môi trường mô phỏng, không phải traffic thật.

### 0:30–1:10 — Baseline

Để chọn **Baseline · swarm**.

> “Đây là mốc tham chiếu: 70 trial. Pass rate là 98,57%; approval bypass và secret leak bằng 0. Mỗi report có run ID và SHA để mình chạy lại cùng dữ liệu.”

Nhắc metric `reply matches ledger` hiển thị 100% vì shape swarm không phát reply event; đây không phải bằng chứng về độ đúng của câu trả lời khách hàng.

### 1:10–1:45 — Bản sửa

Chọn **Bản sửa · fixed**.

> “Bản fixed bỏ lỗi tin ticket hơn dữ liệu DB. Pass rate và số tiền hoàn đúng đều đạt 100%; gate cho qua.”

### 1:45–2:35 — Hồi quy và trace

Chọn **Hồi quy · seeded**.

> “Ở bản này, pass rate giảm còn 71,43%. Gate chặn thay vì chỉ báo điểm trung bình. Trace cho thấy event 3 là `model_override`: ticket ghi trễ 5 ngày đã ghi đè DB. Sau đó agent tạo quote 20.000đ và hoàn tiền, trong khi label kỳ vọng 0đ.”

Chỉ vào dòng event 3 và quyết định BLOCK. Nêu paired CI của pass rate: Δ −0,271; CI 95% [−0,500, −0,057], nằm dưới 0.

### 2:35–3:00 — Judge cũng được đánh giá

> “Không mặc định tin LLM-as-a-judge. Judge tone đạt κ 0,757, precision 0,857, recall 0,8 trên replay. Judge helpful chỉ recall 0,3, bỏ sót 21 trên 30 lỗi nên không dùng làm release gate. Tiền và approval luôn chấm bằng code.”

## Nếu có thêm 2 phút

- Mở `docs/failure_taxonomy.md`: chỉ ra cách trace được gắn thành FM-03 `ticket_trust` và grader `DbFactKept`.
- Mở `docs/judge_audit.md`: đọc một bất đồng H-008 để cho thấy rubric được sửa từ ví dụ cụ thể.
- Chạy CLI để chứng minh report được sinh bởi script, không chỉnh tay:

```powershell
cd src
.\.venv\Scripts\python.exe -m lab9.eval --shape fixed --spec config/metric_spec.yaml --out reports/eval_fixed.json
.\.venv\Scripts\python.exe -m lab9.gate --pr reports/eval_fixed.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml
```

Để chứng minh gate chặn regression:

```powershell
.\.venv\Scripts\python.exe -m lab9.eval --shape seeded_regression --spec config/metric_spec.yaml --out reports/eval_seeded_regression.json
.\.venv\Scripts\python.exe -m lab9.gate --pr reports/eval_seeded_regression.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml
```

Lệnh thứ hai dự kiến exit 1 vì bản này bị chặn. Đây là kết quả mong muốn của gate, không phải lỗi demo.

## Câu hỏi thường gặp

- **“Có bảo đảm không bao giờ sai không?”** Không. Đây là 14 ca × 5 seed với MockLLM; hồi quy hiếm hoặc ngoài tập vẫn có thể lọt.
- **“Vì sao không dùng judge helpful?”** Recall 0,3 thấp hơn floor 0,7; judge bỏ sót nhiều lỗi theo nhãn người.
- **“Vì sao so theo item thay vì so hai trung bình?”** Paired bootstrap ghép cùng item giữa baseline và PR; CI cho biết mức giảm có ý nghĩa hay chưa.
- **“Tại sao metric reply ở baseline là 100%?”** Shape swarm không phát reply event. Đây là giới hạn quan sát; FM-08 cần shape phát reply để kết luận.

## Kết thúc

> “Điều quan trọng không phải một con số pass rate riêng lẻ. Ta cần bộ ca cố định, grader đáng tin, trace chỉ ra nguyên nhân và gate tái lập được trước khi merge.”
