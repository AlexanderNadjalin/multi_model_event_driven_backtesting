import configparser as cp
import pandas as pd
import strategy.strategy as strat
from holdings.portfolio import Portfolio


class MasterPortfolio:
    def __init__(self,
                 inception_date: str) -> None:
        self.portfolios = {}
        self.strategies = {}
        self.plots = []
        self.metrics = []

        self.config = self.config()
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
    def config() -> cp.ConfigParser:
        """
        Read portfolio_config file and return a config object. Used to set default parameters for holdings objects.
        :return: A ConfigParser object.
        """
        conf = cp.ConfigParser()
        conf.read('holdings/portfolio_config.ini')

        print('INFO: Read portfolio_config.ini file.')
        print(' ')

        return conf

    def create_history_table(self) -> None:
        """
        Create pd.Dataframe to hold daily values of portfolio.
        :return: None.
        """
        if self.benchmark != '':
            self.history = pd.DataFrame(columns=['date',
                                                 'current_cash',
                                                 'total_commission',
                                                 'realized_pnl',
                                                 'unrealized_pnl',
                                                 'total_pnl',
                                                 'total_market_value',
                                                 'benchmark_value'])
        else:
            self.history = pd.DataFrame(columns=['date',
                                                 'current_cash',
                                                 'total_commission',
                                                 'realized_pnl',
                                                 'unrealized_pnl',
                                                 'total_pnl',
                                                 'total_market_value'])

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

    # TODO
    def aggregate(self) -> None:
        """
        Sum all values in the history table.
        :return:
        """
        for p in self.portfolios:
            self.history = self.history.add(p,
                                            fill_value=0)
