# BOT TRADER SWING MULTI V4.1.0 — TRADING MASTER + SWING EXPERT

## Bản chất hệ thống
V4.1.0 kế thừa V4.0.0/V3.1.0/V3.0.0 và bổ sung Chuyên gia Swing Trading 5–20 phiên:
- Trợ lý suy luận giao dịch ngoại tuyến, hợp nhất kỹ thuật, market regime, RS, đa khung, định giá, chất lượng dữ liệu và vị thế.
- Knowledge Hub SQLite lưu tài liệu cục bộ, gắn ticker, loại tài liệu, kỳ báo cáo và nguồn.
- Sổ bằng chứng, luận cứ tích cực/tiêu cực, mâu thuẫn, dữ liệu còn thiếu, kịch bản điều kiện và kế hoạch hành động.
- Xuất hồ sơ suy luận JSON để lưu trữ và đối chiếu theo từng lần phân tích.

**Minh bạch quan trọng:** Trợ lý V4.0 là hệ thống suy luận ngoại tuyến theo luật có thể kiểm toán (explainable rule-based reasoning), KHÔNG phải mô hình ngôn ngữ lớn, không tự học từ giao dịch và không dự báo chắc chắn. Trích đoạn tài liệu được tìm bằng từ khóa; người dùng phải mở tài liệu gốc để xác minh trước khi coi là dữ kiện.

## Các phân hệ
1. Trading Dashboard
2. Money Flow & Liquidity
3. Relative Strength & Sector
4. Quant Lab & Backtest
5. Raw Data & Audit
6. Investment Intelligence
7. Multi-stock Scanner
8. Trợ lý suy luận & Knowledge Hub
9. Chuyên gia Swing Trading (tìm cổ phiếu mới + quản lý vị thế hiện tại)

## Liên kết dữ liệu
OHLCV → kiểm tra chất lượng → chỉ báo → chiến lược/Decision Engine → Market Regime/RS/đa khung → Risk Engine → Trợ lý suy luận.
Tài liệu được gắn mã cổ phiếu, loại tài liệu, kỳ và nguồn. Trợ lý chỉ đưa tài liệu liên quan vào sổ bằng chứng; không tự biến văn bản chưa xác minh thành số liệu tài chính.

## Cài đặt Windows
1. Giải nén ZIP.
2. Mở thư mục `BOT_TRADER_SWING_MULTI_V4.1.0`.
3. Chạy `install_windows.bat`.
4. Chạy `run_windows.bat`.

## Cài đặt thủ công
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Dữ liệu và tài liệu
- OHLCV: CSV/XLSX/TXT/JSON/Parquet theo schema có sẵn.
- Knowledge Hub: PDF có lớp text, DOCX, XLSX/XLS, CSV, TXT, MD, JSON.
- PDF scan ảnh cần OCR trước; hệ thống không tự OCR.
- SQLite `trading_knowledge.db` được tạo cục bộ trong thư mục chạy app.
- Không nạp dữ liệu định danh/tài khoản môi giới, mật khẩu hoặc thông tin nhạy cảm.

## Kiểm thử
```bash
pytest -q
```

## Giới hạn và an toàn
- Không kết nối API AI bên ngoài; không đặt lệnh tự động.
- Không có xác suất thắng được hiệu chỉnh thống kê; điểm xếp hạng không phải xác suất.
- Báo cáo tài chính/định giá phụ thuộc dữ liệu người dùng nhập và phải kiểm tra kỳ, đơn vị, nguồn.
- Backtest không đại diện hiệu suất tương lai; cần kiểm định ngoài mẫu và kiểm tra thiên lệch sống sót/nhìn trước.
- Không xem đầu ra là khuyến nghị mua/bán cá nhân.


## V4.0 — Trading Master

Xem `ARCHITECTURE_V4.0.md`, `USER_GUIDE_V4.0.md` và `CHANGELOG_V4.0.0.md`. V4.0 bổ sung lớp điều phối suy luận và nhật ký quyết định ngoại tuyến. Đây là hệ thống rule-based có thể kiểm toán, không phải LLM tự học hoặc công cụ tự đặt lệnh.


## V4.1 — Chuyên gia Swing Trading

Cấu hình đã chốt: phạm vi BOTH (tìm cổ phiếu mới và quản lý vị thế đang nắm), kỳ vọng 5–20 phiên, phong cách CÂN BẰNG. Tab 9 dùng chung OHLCV, chỉ báo, Market Regime, RS benchmark/ngành, Risk Manager và Knowledge Hub. Có bộ lọc Breakout/Pullback/Base, kế hoạch trigger/invalidation/target/R:R, sizing tham chiếu, quản lý vị thế và scanner đa mã.

Đọc `SWING_TRADING_SPEC_V4.1.md`, `ARCHITECTURE_V4.1.md`, `USER_GUIDE_V4.1.md` và `CHANGELOG_V4.1.0.md`. Điểm Swing là heuristic, không phải xác suất; bộ tiêu chí chưa được walk-forward validation riêng.
