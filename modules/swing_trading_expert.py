"""Swing Trading Expert for 5-20 sessions.

Deterministic, explainable research engine. It does not predict prices or execute orders.
All thresholds are transparent heuristics and must be validated with out-of-sample tests.
"""
from __future__ import annotations
from typing import Any
import math
import pandas as pd
from .indicators import add_indicators
from .risk_manager import calculate_position_size

HORIZON_SESSIONS = (5, 20)
DEFAULT_STYLE = "CÂN BẰNG"


def _num(value: Any) -> float | None:
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def _market_gate(regime: dict | None) -> tuple[str, list[str]]:
    regime = regime or {}
    name = str(regime.get("regime", "CHƯA CÓ DỮ LIỆU")).upper()
    reasons = list(regime.get("reasons", []) or [])
    if any(x in name for x in ("GIẢM", "BEAR", "DOWN")):
        return "DEFENSIVE", ["Thị trường chung bất lợi: hạ mức quyết liệt, yêu cầu xác nhận mạnh hơn."] + reasons
    if any(x in name for x in ("TĂNG", "BULL", "UP")):
        return "SUPPORTIVE", ["Thị trường chung tương đối thuận lợi cho chiến lược theo xu hướng."] + reasons
    return "NEUTRAL", ["Thị trường chung chưa xác nhận xu hướng thuận lợi rõ ràng."] + reasons


def analyze_swing_setup(enriched: pd.DataFrame, market_regime: dict | None = None,
                        rs_market: dict | None = None, rs_sector: dict | None = None,
                        documents: list[dict] | None = None,
                        capital_vnd: float = 100_000_000, risk_pct: float = 1.0,
                        max_allocation_pct: float = 20.0, lot_size: int = 100,
                        position: dict | None = None, risk_style: str = DEFAULT_STYLE) -> dict:
    """Build a 5-20 session swing plan from an enriched single-symbol OHLCV frame."""
    position = position or {}
    documents = documents or []
    if enriched is None or len(enriched) < 50:
        return {"status": "INSUFFICIENT_DATA", "symbol": None, "horizon_sessions": "5-20",
                "setup": "CHƯA ĐỦ DỮ LIỆU", "score": None,
                "reasons": ["Cần tối thiểu 50 phiên dữ liệu OHLCV hợp lệ."],
                "blockers": ["Thiếu lịch sử giá tối thiểu"], "documents": documents}

    x = enriched.sort_values("date").reset_index(drop=True).copy()
    last, prev = x.iloc[-1], x.iloc[-2]
    symbol = str(last.get("symbol", "UNKNOWN"))
    close, high, low = _num(last.get("close")), _num(last.get("high")), _num(last.get("low"))
    ma20, ma50 = _num(last.get("SMA20")), _num(last.get("SMA50"))
    rsi, atr = _num(last.get("RSI14")), _num(last.get("ATR14"))
    relvol, adx = _num(last.get("REL_VOLUME20")), _num(last.get("ADX14"))
    macdh = _num(last.get("MACD_HIST"))
    needed = {"close": close, "high": high, "low": low, "SMA20": ma20,
              "SMA50": ma50, "RSI14": rsi, "ATR14": atr, "REL_VOLUME20": relvol,
              "MACD_HIST": macdh}
    missing = [k for k, v in needed.items() if v is None]
    if missing or close is None or close <= 0 or atr is None or atr <= 0:
        return {"status": "INSUFFICIENT_DATA", "symbol": symbol, "horizon_sessions": "5-20",
                "setup": "CHƯA ĐỦ DỮ LIỆU", "score": None,
                "reasons": ["Thiếu hoặc sai chỉ báo: " + ", ".join(missing)],
                "blockers": ["Không lập vùng giá khi dữ liệu đầu vào chưa hợp lệ"], "documents": documents}

    reasons: list[str] = []
    positives: list[str] = []
    negatives: list[str] = []
    blockers: list[str] = []
    score = 0

    trend_up = close > ma20 > ma50
    trend_down = close < ma20 < ma50
    if trend_up:
        score += 20; positives.append("Cấu trúc giá trên MA20 và MA50, MA20 nằm trên MA50.")
    elif trend_down:
        score -= 25; negatives.append("Cấu trúc giá dưới MA20 và MA50: xu hướng ngắn-trung hạn yếu.")
    else:
        positives.append("Xu hướng chưa đồng thuận hoàn toàn; cần xác nhận cấu trúc giá.")

    if 50 <= rsi <= 68:
        score += 12; positives.append(f"RSI14={rsi:.1f}: động lượng tích cực, chưa ở vùng quá nóng theo ngưỡng tham chiếu.")
    elif rsi > 75:
        score -= 8; negatives.append(f"RSI14={rsi:.1f}: động lượng cao, rủi ro mua đuổi tăng.")
    elif rsi < 40:
        score -= 8; negatives.append(f"RSI14={rsi:.1f}: động lượng yếu; chưa mặc định đây là tín hiệu bắt đáy.")
    else:
        score += 3; reasons.append(f"RSI14={rsi:.1f}: vùng trung tính, cần thêm xác nhận.")

    if relvol >= 1.3:
        score += 15; positives.append(f"Relative Volume={relvol:.2f}x: thanh khoản cao hơn nền 20 phiên.")
    elif relvol >= 1.0:
        score += 8; positives.append(f"Relative Volume={relvol:.2f}x: khối lượng đạt/xấp xỉ trung bình.")
    else:
        score -= 8; negatives.append(f"Relative Volume={relvol:.2f}x: thanh khoản chưa xác nhận mạnh.")

    if macdh >= 0:
        score += 8; positives.append("MACD Histogram không âm, động lượng chưa suy yếu theo tiêu chí này.")
    else:
        score -= 6; negatives.append("MACD Histogram âm, cần thận trọng với động lượng giảm.")

    if adx is not None:
        if adx >= 25:
            score += 8; positives.append(f"ADX14={adx:.1f}: cường độ xu hướng tương đối rõ; cần đối chiếu hướng DI nếu có.")
        elif adx < 15:
            score -= 3; reasons.append(f"ADX14={adx:.1f}: xu hướng yếu, chiến lược theo xu hướng có thể kém hiệu quả.")

    # Transparent 20-session structures. A breakout is confirmed only on the latest close.
    prior = x.iloc[-21:-1]
    prior_high = _num(prior.high.max()) if len(prior) == 20 else None
    prior_low = _num(prior.low.min()) if len(prior) == 20 else None
    breakout = prior_high is not None and close > prior_high and relvol >= 1.3
    pullback = trend_up and abs(close - ma20) <= 0.75 * atr and rsi >= 45
    base_range_pct = None
    if len(prior) == 20 and prior_low and prior_low > 0:
        base_range_pct = (prior_high - prior_low) / prior_low * 100
    base = base_range_pct is not None and base_range_pct <= 12 and close >= ma20

    if breakout:
        setup = "BREAKOUT"
        score += 15
        positives.append(f"Đóng cửa vượt đỉnh 20 phiên trước với Relative Volume={relvol:.2f}x.")
        reasons.append("Breakout chỉ được xác nhận theo giá đóng cửa; cần theo dõi nguy cơ false breakout.")
    elif pullback:
        setup = "PULLBACK"
        score += 12
        positives.append("Giá đang kiểm tra vùng MA20 trong cấu trúc xu hướng tăng; cần nến xác nhận.")
    elif base:
        setup = "BASE / TÍCH LŨY"
        score += 7
        positives.append(f"Biên độ nền 20 phiên khoảng {base_range_pct:.1f}%; cần xác nhận cung-cầu trước khi kết luận breakout.")
    else:
        setup = "CHƯA CÓ MÔ HÌNH RÕ"
        reasons.append("Chưa đạt tiêu chí breakout, pullback hoặc nền tích lũy theo bộ lọc hiện tại.")

    gate, gate_reasons = _market_gate(market_regime)
    reasons.extend(gate_reasons)
    if gate == "SUPPORTIVE": score += 8
    elif gate == "DEFENSIVE": score -= 15; blockers.append("Bối cảnh thị trường chung đang bất lợi")

    for label, rs in (("VN-Index", rs_market or {}), ("ngành", rs_sector or {})):
        rel = _num(rs.get("relative_return_pct"))
        if rel is None:
            reasons.append(f"Chưa có dữ liệu RS đồng bộ so với {label}.")
        elif rel > 0:
            score += 5; positives.append(f"Sức mạnh tương đối đang vượt {label} ({rel:+.2f}%).")
        else:
            score -= 5; negatives.append(f"Sức mạnh tương đối yếu hơn {label} ({rel:+.2f}%).")

    # A reference plan, not an executable order. Use recent structure + ATR for invalidation.
    recent_support = _num(x.low.tail(10).min())
    structural_stop = min(recent_support, close - 1.5 * atr) if recent_support is not None else close - 1.5 * atr
    stop = max(0.01, structural_stop)
    trigger = max(close, high) + 0.1 * atr
    risk_per_share = trigger - stop
    target_1 = trigger + 1.5 * risk_per_share
    target_2 = trigger + 2.0 * risk_per_share
    rr_1 = (target_1 - trigger) / risk_per_share if risk_per_share > 0 else None
    rr_2 = (target_2 - trigger) / risk_per_share if risk_per_share > 0 else None
    if rr_1 is None or rr_1 < 1.5:
        blockers.append("Tỷ lệ lợi nhuận/rủi ro tham chiếu không đạt 1.5R")

    sizing = calculate_position_size(capital_vnd, trigger, stop, risk_pct,
                                     max_allocation_pct, lot_size, 1.0)
    if sizing.get("quantity", 0) <= 0:
        blockers.append("Quy mô vị thế tính theo giới hạn rủi ro hiện tại bằng 0")

    # Position management is distinct from new-entry logic.
    quantity = int(position.get("quantity", 0) or 0)
    entry_price = _num(position.get("entry_price"))
    position_report = {"mode": "NEW_ENTRY" if quantity <= 0 else "MANAGE_EXISTING",
                       "quantity": quantity, "entry_price": entry_price}
    if quantity > 0:
        if entry_price is None or entry_price <= 0:
            blockers.append("Đã khai báo số lượng nắm giữ nhưng thiếu giá vốn hợp lệ")
            position_report["status"] = "NEED_ENTRY_PRICE"
        else:
            held_stop = max(0.01, min(entry_price - 1.5 * atr, recent_support if recent_support else entry_price - 1.5 * atr))
            pnl_pct = (close / entry_price - 1) * 100
            position_report.update({"market_price": close, "pnl_pct_before_costs": pnl_pct,
                                    "reference_invalidation": held_stop,
                                    "distance_to_invalidation_pct": (close / held_stop - 1) * 100 if held_stop > 0 else None,
                                    "status": "REVIEW_RISK" if close <= held_stop else "MONITOR"})
            if close <= held_stop:
                blockers.append("Giá đóng cửa đã chạm/vượt xuống mức vô hiệu tham chiếu của vị thế")

    if risk_style.upper().startswith("THẬN"):
        min_score, min_relvol = 70, 1.2
    elif "CAO" in risk_style.upper() or "AGGRESSIVE" in risk_style.upper():
        min_score, min_relvol = 55, 1.0
    else:
        min_score, min_relvol = 65, 1.1
    if relvol < min_relvol:
        blockers.append(f"Relative Volume chưa đạt ngưỡng phong cách {risk_style}: cần >= {min_relvol:.1f}x")
    if trend_down:
        blockers.append("Xu hướng giá đang giảm đồng pha")
    if setup == "CHƯA CÓ MÔ HÌNH RÕ":
        blockers.append("Chưa có cấu trúc Swing Trading rõ ràng")
    if not documents:
        reasons.append("Chưa có tài liệu doanh nghiệp liên kết; cần bổ sung để hoàn thiện luận điểm cơ bản.")

    score = max(0, min(100, int(score)))
    if blockers or score < min_score:
        status = "WAIT_OR_NO_TRADE"
        conclusion = "CHỜ XÁC NHẬN / CHƯA GIAO DỊCH"
    elif quantity > 0:
        status = "MANAGE_POSITION"
        conclusion = "ƯU TIÊN QUẢN LÝ VỊ THẾ HIỆN TẠI"
    else:
        status = "WATCH_ENTRY"
        conclusion = "ĐƯA VÀO DANH SÁCH CHỜ KÍCH HOẠT"

    if quantity > 0:
        next_steps = ["Đối chiếu giá hiện tại với giá vốn, mức vô hiệu và tỷ trọng danh mục.",
                      "Không gia tăng vị thế chỉ vì giá giảm; chỉ đánh giá lại khi luận điểm và rủi ro được cập nhật.",
                      "Theo dõi đóng cửa, thanh khoản và cấu trúc hỗ trợ trong 5-20 phiên."]
    else:
        next_steps = ["Chờ giá đóng cửa xác nhận điều kiện kích hoạt; không mua chỉ vì chạm vùng giá.",
                      "Kiểm tra lại thị trường chung, RS, thanh khoản và tài liệu doanh nghiệp trước khi quyết định.",
                      "Nếu điều kiện vô hiệu xuất hiện hoặc R:R không còn đạt, hủy kế hoạch thay vì đuổi giá."]

    return {
        "symbol": symbol, "status": status, "conclusion": conclusion,
        "horizon_sessions": "5-20", "risk_style": risk_style,
        "setup": setup, "score": score, "score_is_probability": False,
        "market_gate": gate, "reasons": reasons, "positives": positives,
        "negatives": negatives, "blockers": blockers, "next_steps": next_steps,
        "plan": {"reference_trigger": trigger, "invalidation": stop,
                 "target_1": target_1, "target_2": target_2,
                 "rr_target_1": rr_1, "rr_target_2": rr_2,
                 "atr14": atr, "prior_20d_high": prior_high,
                 "prior_20d_low": prior_low},
        "position": position_report, "sizing": sizing,
        "evidence": {"close": close, "ma20": ma20, "ma50": ma50,
                     "rsi14": rsi, "rel_volume20": relvol, "adx14": adx,
                     "macd_hist": macdh, "rs_market": rs_market or {},
                     "rs_sector": rs_sector or {}, "documents": documents[:8]},
        "limitations": ["Điểm Swing là điểm heuristic để xếp hạng, không phải xác suất sinh lời.",
                        "Vùng kích hoạt/vô hiệu/mục tiêu là mức tham chiếu tính từ dữ liệu lịch sử; không phải lệnh giao dịch.",
                        "Chưa có kiểm định walk-forward riêng cho bộ tiêu chí Swing 5-20 phiên."],
    }


def scan_swing_universe(data: pd.DataFrame, market_regime: dict | None = None,
                        capital_vnd: float = 100_000_000, risk_pct: float = 1.0,
                        max_allocation_pct: float = 20.0, lot_size: int = 100,
                        risk_style: str = DEFAULT_STYLE) -> pd.DataFrame:
    """Rank eligible symbols for research; never treats ranking as a buy signal."""
    rows = []
    if data is None or data.empty or "symbol" not in data:
        return pd.DataFrame(columns=["symbol", "score", "setup", "status", "close", "rel_volume20"])
    for symbol, frame in data.groupby("symbol"):
        try:
            enriched = add_indicators(frame.sort_values("date").copy())
            report = analyze_swing_setup(enriched, market_regime=market_regime,
                                         capital_vnd=capital_vnd, risk_pct=risk_pct,
                                         max_allocation_pct=max_allocation_pct,
                                         lot_size=lot_size, risk_style=risk_style)
            if report.get("score") is None:
                continue
            p = report["plan"]
            e = report["evidence"]
            rows.append({"symbol": str(symbol), "score": report["score"],
                         "setup": report["setup"], "status": report["conclusion"],
                         "close": e["close"], "rel_volume20": e["rel_volume20"],
                         "trigger_ref": p["reference_trigger"],
                         "invalidation_ref": p["invalidation"],
                         "target_1_ref": p["target_1"],
                         "blockers": "; ".join(report["blockers"]),
                         "reasons": "; ".join(report["positives"][:3])})
        except Exception:
            # A malformed symbol is skipped; scanner continues for other symbols.
            continue
    if not rows:
        return pd.DataFrame(columns=["symbol", "score", "setup", "status", "close", "rel_volume20"])
    return pd.DataFrame(rows).sort_values(["score", "symbol"], ascending=[False, True]).reset_index(drop=True)
