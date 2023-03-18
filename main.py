import market.markets as m
from holdings import portfolio_master, portfolio
import backtest.backtest as bt
import strategy.strategy as strat


if __name__ == '__main__':
    start_date = '2023-01-02'
    end_date='2023-01-05'

    market = m.Markets(fill_missing_method=None)

    mp = portfolio_master.MasterPortfolio(inception_date=start_date)
    p1 = portfolio.Portfolio(init_cash=50000.0,
                             benchmark='^OMX',
                             pf_id='1')
    p2 = portfolio.Portfolio(init_cash=50000.0,
                             benchmark='^OMX',
                             pf_id='2')
    mp.add_portfolio(pf=p1)
    mp.add_portfolio(pf=p2)

    s1 = strat.BuyAndHold(id_num_shares={'^OMX': 100})
    s2 = strat.BuyAndHold(id_num_shares={'^OMX': 200})
    mp.add_strategy(s1)
    mp.add_strategy(s2)

    test = bt.Backtests(market=market,
                        mpf=mp,
                        start_date=start_date,
                        end_date=end_date)

    # TODO loop all portfolios
    # TODO signals working
    test.run()

    quit()
