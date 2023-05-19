import market.markets as m
from holdings import portfolio_master, portfolio
import backtest.backtest as bt
import strategy.strategy as strat
from plot.plot import Plot


if __name__ == '__main__':
    start_date = '2020-12-30'
    end_date = '2023-03-06'

    market = m.Markets(fill_missing_method=None)

    mp = portfolio_master.MasterPortfolio(inception_date=start_date)
    p1 = portfolio.Portfolio(init_cash=500000.0,
                             benchmark='^OMX_Close',
                             pf_id='pf1')
    p2 = portfolio.Portfolio(init_cash=500000.0,
                             benchmark='^OMX_Close',
                             pf_id='pf2')
    mp.add_portfolio(pf_id=p1.pf_id,
                     pf=p1)
    mp.add_portfolio(pf_id=p2.pf_id,
                     pf=p2)

    s1 = strat.BuyAndHold(id_num_shares={'^OMX_Close': 100})
    s2 = strat.BuyAndHold(id_num_shares={'^OMX_Close': 200})
    mp.add_strategy(pf_id=p1.pf_id,
                    st=s1)
    mp.add_strategy(pf_id=p2.pf_id,
                    st=s2)

    test = bt.Backtests(market=market,
                        mpf=mp,
                        start_date=start_date,
                        end_date=end_date,
                        verbose=False)

    test.run()

    p = Plot(bt=test)
    p.drawdowns_plot(pf_list=[mp],
                     save=False)
    p.rolling_sharpe_beta_plot(pf_list=[mp])

    quit()
