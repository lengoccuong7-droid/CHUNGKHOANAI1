import numpy as np
import pandas as pd
from modules.indicators import add_indicators
from modules.swing_trading_expert import analyze_swing_setup, scan_swing_universe


def _uptrend_frame(symbol='AAA', n=260):
    dates = pd.bdate_range('2025-01-01', periods=n)
    close = np.linspace(10000, 15000, n) + np.sin(np.arange(n) / 5) * 80
    volume = np.full(n, 1_000_000.0)
    volume[-1] = 1_500_000
    return pd.DataFrame({
        'date': dates, 'symbol': symbol,
        'open': close - 30, 'high': close + 100,
        'low': close - 100, 'close': close, 'volume': volume,
    })


def test_swing_report_has_5_20_horizon_and_risk_plan():
    enriched = add_indicators(_uptrend_frame())
    report = analyze_swing_setup(
        enriched, market_regime={'regime': 'TĂNG'},
        rs_market={'relative_return_pct': 2.0},
        rs_sector={'relative_return_pct': 1.0},
        documents=[{'filename': 'AAA_Q3.pdf', 'excerpt': 'BCTC Q3'}],
        capital_vnd=100_000_000, risk_pct=1, max_allocation_pct=20,
    )
    assert report['horizon_sessions'] == '5-20'
    assert report['risk_style'] == 'CÂN BẰNG'
    assert report['score'] is not None
    assert report['plan']['reference_trigger'] > report['plan']['invalidation']
    assert report['plan']['target_1'] > report['plan']['reference_trigger']
    assert 'score_is_probability' in report and report['score_is_probability'] is False


def test_swing_position_management_is_separate_from_new_entry():
    enriched = add_indicators(_uptrend_frame())
    report = analyze_swing_setup(
        enriched, market_regime={'regime': 'TĂNG'},
        position={'quantity': 1000, 'entry_price': 12000},
    )
    assert report['position']['mode'] == 'MANAGE_EXISTING'
    assert report['position']['quantity'] == 1000
    assert 'pnl_pct_before_costs' in report['position']


def test_swing_scanner_returns_ranked_dataframe():
    data = pd.concat([_uptrend_frame('AAA'), _uptrend_frame('BBB')], ignore_index=True)
    result = scan_swing_universe(data, market_regime={'regime': 'TĂNG'})
    assert isinstance(result, pd.DataFrame)
    assert set(result['symbol']) == {'AAA', 'BBB'}
    assert result['score'].is_monotonic_decreasing
