import pandas as pd
import pytest

import backlight.datasource
import backlight.positions
from backlight.trades import trades as tr
from backlight.asset.currency import Currency
from backlight.metrics import evaluation_metrics as module
from backlight.metrics.position_metrics import (
    _trade_amount,
    calculate_position_performance,
)


@pytest.fixture
def symbol():
    return "USDJPY"


@pytest.fixture
def currency_unit():
    return Currency.JPY


@pytest.fixture
def market(symbol, currency_unit):
    data = [[1.0], [2.0], [3.0], [4.0], [5.0], [6.0], [7.0], [8.0], [9.0], [9.0]]
    df = pd.DataFrame(
        index=pd.date_range(start="2018-06-06", freq="1D", periods=len(data)),
        data=data,
        columns=["mid"],
    )
    return backlight.datasource.from_dataframe(df, symbol, currency_unit)


@pytest.fixture
def trades(symbol, currency_unit):
    data = [1.0, -2.0, 1.0, 2.0, -4.0, 2.0, 1.0, 0.0, 1.0, 0.0]
    index = pd.date_range(start="2018-06-06", freq="1D", periods=len(data))
    trades = []
    for i in range(0, len(data), 2):
        trade = pd.Series(index=index[i : i + 2], data=data[i : i + 2], name="amount")
        trades.append(trade)
    trades = tr.make_trades(symbol, trades, currency_unit)
    return trades


@pytest.fixture
def positions(trades, market):
    # positions should be
    # data = [
    #     [1.0, 1.0, -1.0],  # value = 0.0, pl = None
    #     [-1.0, 2.0, 3.0],  # value = 1.0, pl = 1.0
    #     [0.0, 3.0, 0.0],  # value = 0.0, pl = -1.0
    #     [2.0, 4.0, -8.0],  # value = 0.0, pl = 0.0
    #     [-2.0, 5.0, 12.0],  # value = 2.0, pl = 2.0
    #     [0.0, 6.0, 0.0],  # value = 0.0, pl = -2.0
    #     [1.0, 7.0, -7.0],  # value = 0.0, pl = 0.0
    #     [1.0, 8.0, -7.0],  # value = 1.0, pl = 1.0
    #     [2.0, 9.0, -16.0],  # value = 2.0, pl = 1.0
    #     [2.0, 9.0, -16.0],  # value = 2.0, pl = 0.0
    # ]
    # columns = ["amount", "price", "principal"]
    principal = 100.0
    return backlight.positions.calculate_positions(trades, market, principal=principal)


def test_calculate_pl(positions):
    expected = pd.Series(
        data=[0.0, 1.0, -1.0, 0.0, 2.0, -2.0, 0.0, 1.0, 1.0, 0.0],
        index=positions.index[1:],
        name="pl",
    )
    assert (module.calculate_pl(positions) == expected).all()


def test__trade_amount(positions):
    expected = 14.0
    assert _trade_amount(positions.amount) == expected


def test_calculate_sharpe(positions):
    expected = 2.9452967928116256
    assert module.calculate_sharpe(positions, freq=pd.Timedelta("1D")) == expected


def test_calculate_drawdown(positions):
    expected = pd.Series(
        data=[0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 2.0, 2.0, 1.0, 0.0, 0.0],
        index=positions.index,
    )
    assert (module.calculate_drawdown(positions) == expected).all()


def test_calculate_position_performance(positions):
    metrics = calculate_position_performance(positions)
    expected_total_pl = 2.0
    expected_win_pl = 5.0
    expected_lose_pl = -3.0
    expected_trade_amount = 14.0
    expected_sharpe = 2.9452967928116256
    expected_avg_pl = expected_total_pl / expected_trade_amount
    assert metrics.loc["metrics", "total_pl"] == expected_total_pl
    assert metrics.loc["metrics", "total_win_pl"] == expected_win_pl
    assert metrics.loc["metrics", "total_lose_pl"] == expected_lose_pl
    assert metrics.loc["metrics", "cnt_amount"] == expected_trade_amount
    assert metrics.loc["metrics", "avg_pl_per_amount"] == expected_avg_pl
    assert metrics.loc["metrics", "sharpe"] == expected_sharpe
