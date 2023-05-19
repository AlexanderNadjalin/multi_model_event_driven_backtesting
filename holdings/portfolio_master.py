import configparser as cp
import pandas as pd
import strategy.strategy as strat
from holdings.portfolio import Portfolio
from market.markets import Markets


class MasterPortfolio:
    def __init__(self,
                 inception_date: str) -> None:
        self.portfolios = {}
        self.strategies = {}
        self.strategy_names = {}
        self.plots = []
        self.metrics = []

        self.config, self.metrics_config = self.config()
        self.type = 'MasterPortfolio'
        self.commission = self.config['commission']['commission_scheme']
        self.init_cash = float(self.config['init_cash']['init_cash'])
        self.accum_init_cash = 0
        self.currency = self.config['portfolio_information']['currency']
        self.current_cash = self.init_cash
        self.inception_date = inception_date
        self.current_date = self.inception_date
        self.benchmark = self.config['benchmark']['benchmark_name']
        self.pf_id = self.config['portfolio_information']['pf_id']
        self.history = pd.DataFrame()
        self.records = pd.DataFrame()
        self.create_history_table()

        print('SUCCESS: Master Portfolio ' + self.pf_id + ' created.')

    @ staticmethod
    def config() -> (cp.ConfigParser, cp.ConfigParser):
        """
        Read portfolio_config file and metric_config files.
        Return a config object for portfolio, and one for metrics.
        Used to set default parameters for holdings and metrics objects.
        :return: Two ConfigParser objects.
        """
        conf = cp.ConfigParser()
        conf.read('holdings/portfolio_config.ini')
        m_conf = cp.ConfigParser()
        m_conf.read('metric/metric_config.ini')

        print('INFO: Read portfolio_config.ini file.')
        print(' ')

        return conf, m_conf

    def create_history_table(self) -> None:
        """
        Create pd.Dataframe to hold daily values of portfolio.
        :return: None.
        """
        self.history = pd.DataFrame(columns=['date',
                                             'current_cash',
                                             'total_commission',
                                             'realized_pnl',
                                             'unrealized_pnl',
                                             'total_pnl',
                                             'total_market_value',
                                             'benchmark_value'])
        self.history.set_index('date',
                               inplace=True)

    def add_portfolio(self,
                      pf_id: str,
                      pf: Portfolio) -> None:
        self.accum_init_cash += pf.init_cash
        if self.accum_init_cash > self.init_cash:
            print('CRITICAL: Master Portfolio´s initial cash exceeded. Aborted.')
            quit()
        else:
            self.portfolios[pf_id] = pf

    def add_strategy(self,
                     pf_id: str,
                     st: strat) -> None:
        """
        Add a strategy to a portfolio id.
        :param pf_id: Portfolio id.
        :param st: Strategy.
        :return: None.
        """
        self.strategies[pf_id] = st

    def update_bench_mark(self,
                          date: str,
                          market: Markets) -> None:
        """
        Aggregate all portfolio history collumn values for this date. Add benchmark value for MasterPortfolio.
        :param date: Date.
        :param market: Markets object.
        :return: None.
        """
        current_cash = 0
        total_commission = 0
        realized_pnl = 0
        unrealized_pnl = 0
        total_pnl = 0
        total_market_value = 0

        # Add a new day's aggregated data for the Master Portfolio.
        for pf in self.portfolios:
            port = self.portfolios.get(pf)
            current_cash += port.history.loc[date, 'current_cash']
            total_commission += port.history.loc[date, 'total_commission']
            realized_pnl += port.history.loc[date, 'realized_pnl']
            unrealized_pnl += port.history.loc[date, 'unrealized_pnl']
            total_pnl += port.history.loc[date, 'total_pnl']
            total_market_value += port.history.loc[date, 'total_market_value']
        # Add the Master Portfolio's benchmark value.
        bm = market.select([self.benchmark],
                           start_date=date,
                           end_date=date)
        bm = bm.iloc[0, 0]
        row = [current_cash,
               total_commission,
               realized_pnl,
               unrealized_pnl,
               total_pnl,
               total_market_value,
               bm]
        self.history.loc[date] = row
