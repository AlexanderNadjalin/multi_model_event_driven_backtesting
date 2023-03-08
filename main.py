import market.markets as m
import holdings.portfolio as pf
import backtest.backtest as bt


if __name__ == '__main__':
    market = m.Markets(fill_missing_method=None)

    port = pf.Portfolio(inception_date='2023-01-02')

    test = bt.Backtest(market=market,
                       pf=port,
                       start_date='2023-01-02',
                       end_date='2023-01-05')

    quit()
