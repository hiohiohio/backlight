import pytest
import pandas as pd
import numpy as np
from backlight.portfolio.portfolio import construct_portfolio as module
from backlight.portfolio.portfolio import _fusion_positions
import backlight.positions.positions


import backlight
from backlight.trades.trades import make_trades
from backlight.asset.currency import Currency
from backlight.positions.positions import Positions
from backlight.portfolio.portfolio import Portfolio


@pytest.fixture
def trades():
    trades = []
    index = [
        "2018-06-06 00:00:00",
        "2018-06-06 00:01:00",
        "2018-06-06 00:02:00",
        "2018-06-06 00:03:00",
        "2018-06-06 00:03:00",
        "2018-06-06 00:04:00 ",
        "2018-06-06 00:05:00",
        "2018-06-06 00:05:00",
        "2018-06-06 00:06:00 ",
        "2018-06-06 00:06:00 ",
        "2018-06-06 00:07:00 ",
        "2018-06-06 00:08:00 ",
        "2018-06-06 00:09:00 ",
        "2018-06-06 00:09:00 ",
    ]

    trade = pd.Series(
        index=pd.to_datetime(index),
        data=[1, -1, -1, 1, 1, 1, -1, -1, -1, -1, 1, 1, 1, -1],
        name="amount",
    )
    ids = [0, 1, 0, 1, 2, 3, 2, 4, 3, 5, 4, 5, 6, 6]
    currency_unit = Currency.JPY

    trades.append(make_trades("USDJPY", [trade], currency_unit, [ids]))
    trades.append(make_trades("EURJPY", [trade], currency_unit, [ids]))
    trades.append(make_trades("USDJPY", [trade], currency_unit, [ids]))
    return trades


@pytest.fixture
def markets():
    markets = []
    symbol = "USDJPY"
    currency_unit = Currency.JPY
    periods = 13
    df = pd.DataFrame(
        index=pd.date_range(start="2018-06-05 23:57:00", freq="1min", periods=periods),
        data=np.repeat(2, periods)[:, None],
        columns=["mid"],
    )
    markets.append(backlight.datasource.from_dataframe(df, symbol, currency_unit))

    symbol = "EURJPY"
    currency_unit = Currency.JPY
    df = pd.DataFrame(
        index=pd.date_range(start="2018-06-05 23:57:00", freq="1min", periods=periods),
        data=np.repeat(4, periods)[:, None],
        columns=["mid"],
    )
    markets.append(backlight.datasource.from_dataframe(df, symbol, currency_unit))
    return markets


@pytest.fixture
def principal():
    return {"USDJPY": 10, "EURJPY": 10}


@pytest.fixture
def lot_size():
    return {"USDJPY": 2, "EURJPY": 2}


def test_construct_portfolio(trades, markets, principal, lot_size):
    portfolio = module(trades, markets, principal, lot_size, Currency.USD)

    index = [
        "2018-06-05 23:59:00",
        "2018-06-06 00:00:00",
        "2018-06-06 00:01:00",
        "2018-06-06 00:02:00",
        "2018-06-06 00:03:00",
        "2018-06-06 00:04:00 ",
        "2018-06-06 00:05:00",
        "2018-06-06 00:06:00 ",
        "2018-06-06 00:07:00 ",
        "2018-06-06 00:08:00 ",
        "2018-06-06 00:09:00 ",
    ]

    data1 = [
        [0.0, 0.0, 5.0],
        [2.0, 2.0, 1.0],
        [0.0, 2.0, 5.0],
        [-2.0, 2.0, 9.0],
        [2.0, 2.0, 1.0],
        [4.0, 2.0, -3.0],
        [0.0, 2.0, 5.0],
        [-4.0, 2.0, 13.0],
        [-2.0, 2.0, 9.0],
        [0.0, 2.0, 5.0],
        [0.0, 2.0, 5.0],
    ]

    data2 = [
        [0.0, 0.0, 10.0],
        [4.0, 2.0, 6.0],
        [0.0, 2.0, 10.0],
        [-4.0, 2.0, 14.0],
        [4.0, 2.0, 6.0],
        [8.0, 2.0, 2.0],
        [0.0, 2.0, 10.0],
        [-8.0, 2.0, 18.0],
        [-4.0, 2.0, 14.0],
        [0.0, 2.0, 10.0],
        [0.0, 2.0, 10.0],
    ]

    data = [data1, data2]

    for (position, d) in zip(portfolio._positions, data):

        expected = pd.DataFrame(
            index=pd.to_datetime(index),
            data=d,
            columns=["amount", "price", "principal"],
        )
        assert ((expected == position).all()).all()


def test_fusion_positions():
    periods = 3
    data = np.arange(periods * 3).reshape((periods, 3))
    columns = ["amount", "price", "principal"]
    currency_unit = Currency.JPY

    positions_list = []
    df = pd.DataFrame(
        data=data,
        index=pd.date_range("2012-1-1", periods=periods, freq="D"),
        columns=columns,
    )
    symbol = "USDJPY"
    positions_list.append(
        backlight.positions.positions.from_dataframe(df, symbol, currency_unit)
    )

    df = pd.DataFrame(
        data=data,
        index=pd.date_range("2012-1-2", periods=periods, freq="D"),
        columns=columns,
    )
    symbol = "USDJPY"
    positions_list.append(
        backlight.positions.positions.from_dataframe(df, symbol, currency_unit)
    )

    df = pd.DataFrame(
        data=data,
        index=pd.date_range("2012-1-4", periods=periods, freq="D"),
        columns=columns,
    )
    symbol = "EURJPY"
    positions_list.append(
        backlight.positions.positions.from_dataframe(df, symbol, currency_unit)
    )

    fusioned = _fusion_positions(positions_list)

    data1 = np.arange(periods * 3).reshape((periods, 3))
    data2 = [[0, 1, 2], [3, 5, 7], [9, 11, 13], [6, 7, 8]]

    df1 = pd.DataFrame(
        data=data1,
        index=pd.date_range("2012-1-1", periods=periods, freq="D"),
        columns=columns,
    )
    df2 = pd.DataFrame(
        data=data2,
        index=pd.date_range("2012-1-1", periods=periods + 1, freq="D"),
        columns=columns,
    )

    expected = [df1, df2]

    for exp, fus in zip(expected, fusioned):
        assert exp.all().all() == fus.all().all()


@pytest.fixture
def mid_markets():
    markets = []
    symbol = "USDJPY"
    currency_unit = Currency.JPY
    periods = 4
    df = pd.DataFrame(
        index=pd.date_range(start="2018-06-06", freq="1min", periods=periods),
        data=np.array([0, 1, 2, 4]),
        columns=["mid"],
    )
    markets.append(backlight.datasource.from_dataframe(df, symbol, currency_unit))
    return markets


@pytest.fixture
def simple_portfolio():
    ptf = []
    periods = 4
    for symbol, currency_unit in zip(
        ["USDJPY", "EURJPY", "EURUSD"], [Currency.JPY, Currency.JPY, Currency.USD]
    ):
        df = pd.DataFrame(
            index=pd.date_range(start="2018-06-06", freq="1min", periods=periods),
            data=np.arange(3 * periods).reshape((periods, 3)),
            columns=["amount", "price", "principal"],
        )
        p = Positions(df)
        p.symbol = symbol
        p.currency_unit = currency_unit
        ptf.append(p)
    return Portfolio(ptf)


# def test_calculate_pl(simple_portfolio, mid_markets):
#     calculated_portfolio = calculate_pl(simple_portfolio, mid_markets, base_ccy="usd")
#     expected = pd.Series(
#         index=["2018-06-06 00:01:00", "2018-06-06 00:02:00", "2018-06-06 00:03:00"],
#         data=[45.0, 66.0, 76.5],
#     )
#     assert ((expected == calculated_portfolio).all()).all()

#     calculated_portfolio = calculate_pl(simple_portfolio, mid_markets, base_ccy="jpy")
#     expected = pd.Series(
#         index=["2018-06-06 00:01:00", "2018-06-06 00:02:00", "2018-06-06 00:03:00"],
#         data=[45.0, 132.0, 306.0],
#     )
#     assert ((expected == calculated_portfolio).all()).all()
