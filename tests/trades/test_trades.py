from backlight.trades import trades as module

import pytest

import pandas as pd
from backlight.asset.currency import Currency


@pytest.fixture
def symbol():
    return "USDJPY"


@pytest.fixture
def currency_unit():
    return Currency.JPY


@pytest.fixture
def trades(symbol, currency_unit):
    data = [1.0, -2.0, 1.0, 2.0, -4.0, 2.0, 1.0, 0.0, 1.0, 0.0]
    index = pd.date_range(start="2018-06-06", freq="1min", periods=len(data))
    trades = []
    for i in range(0, len(data), 2):
        trade = pd.Series(index=index[i : i + 2], data=data[i : i + 2], name="amount")
        trades.append(trade)
    trades = module.make_trades(symbol, trades, currency_unit)
    return trades


def test_trades_ids(trades):
    expected = [0, 1, 2, 3, 4]
    assert trades.ids == expected


def test_trades_amount(trades):
    data = [1.0, -2.0, 1.0, 2.0, -4.0, 2.0, 1.0, 0.0, 1.0, 0.0]
    index = pd.date_range(start="2018-06-06", freq="1min", periods=len(data))
    expected = pd.Series(data=data, index=index, name="amount")
    pd.testing.assert_series_equal(trades.amount, expected)


def test_trades_get_any(trades):
    data = [1.0, -2.0, -4.0, 2.0]
    index = [
        pd.Timestamp("2018-06-06 00:00:00"),
        pd.Timestamp("2018-06-06 00:01:00"),
        pd.Timestamp("2018-06-06 00:04:00"),
        pd.Timestamp("2018-06-06 00:05:00"),
    ]
    expected = pd.Series(data=data, index=index, name="amount")
    # result = trades.get_any(container_set=[0, 4, 5], gap="minute")
    result = trades.get_any(trades.index.minute.isin([0, 4, 5]))
    pd.testing.assert_series_equal(result.amount, expected)


def test_trades_get_all(trades):
    data = [-4.0, 2.0]
    index = [pd.Timestamp("2018-06-06 00:04:00"), pd.Timestamp("2018-06-06 00:05:00")]
    expected = pd.Series(data=data, index=index, name="amount")
    result = trades.get_all(trades.index.minute.isin([0, 4, 5]))
    pd.testing.assert_series_equal(result.amount, expected)


def test_trades_get_trade(trades):
    data = [1.0, -2.0]
    index = pd.date_range(start="2018-06-06", freq="1min", periods=len(data))
    expected = pd.Series(data=data, index=index, name="amount")
    pd.testing.assert_series_equal(trades.get_trade(0), expected)


def test_make_trade():
    periods = 2
    dates = pd.date_range(start="2018-12-01", periods=periods)
    amounts = range(periods)

    t00 = module.Transaction(timestamp=dates[0], amount=amounts[0])
    t11 = module.Transaction(timestamp=dates[1], amount=amounts[1])
    t01 = module.Transaction(timestamp=dates[0], amount=amounts[1])

    trade = module.make_trade([t00, t11])
    expected = pd.Series(index=dates, data=amounts[:2], name="amount")
    pd.testing.assert_series_equal(trade, expected)

    trade = module.make_trade([t00, t01])
    expected = pd.Series(
        index=[dates[0]], data=[amounts[0] + amounts[1]], name="amount"
    )
    pd.testing.assert_series_equal(trade, expected)

    trade = module.make_trade([t11, t01, t00])
    expected = pd.Series(
        index=dates, data=[amounts[0] + amounts[1], amounts[1]], name="amount"
    )
    pd.testing.assert_series_equal(trade, expected)


@pytest.mark.parametrize(
    "expected_ids, refresh_id",
    [[[0, 1, 2, 3, 4], False], [[0, 5, 1, 6, 2, 7, 3, 8, 4, 9], True]],
)
def test_concat(trades, expected_ids, refresh_id):
    trades1 = trades.copy()
    trades2 = trades.copy()
    result = module.concat([trades1, trades2], refresh_id)

    # check symbol
    expected = trades1.symbol
    assert result.symbol == expected

    # check len
    expected = len(trades1) + len(trades2)
    assert len(result) == expected

    # check ids
    expected = expected_ids
    assert result.ids == expected

    # check amount
    data = trades.amount * 2.0
    index = pd.date_range(start="2018-06-06", freq="1min", periods=len(data))
    expected = pd.Series(data=data, index=index, name="amount")
    pd.testing.assert_series_equal(result.amount, expected)
