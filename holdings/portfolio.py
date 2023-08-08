import pandas as pd
from holdings.transaction import Transaction
from market.markets import Markets
from holdings.position_handler import PositionHandler


class Portfolio:
    """
    Create a Portfolio object.
    Read portfolio_config.ini for starting values.
    Portfolio.history has information on positions, their market values, cash etc.
    Portfolio.records has calculated metrics, if the metrics.py functions are called.
    """
    def __init__(self,
                 init_cash: float,
                 benchmark: str,
                 pf_id: str) -> None:

        self.type = 'Portfolio'
        self.init_cash = init_cash
        self.current_cash = self.init_cash
        self.current_date = None
        self.benchmark = benchmark
        self.pf_id = pf_id
        self.position_handler = PositionHandler()
        self.symbols = []
        self.history = pd.DataFrame()
        self.records = pd.DataFrame()
        self.metrics = pd.DataFrame()

        self.create_history_table()
        self.crete_records_table()
        self.add_symbols()
        print('SUCCESS: Portfolio ' + self.pf_id + ' created.')

    def add_symbols(self):
        """
        Add all symbols
        :return:
        """
        for key, value in self.position_handler.positions.items():
            self.symbols.append(key)

    def update_all_market_values(self,
                                 date: str,
                                 market_data: Markets) -> None:
        """
        Update current date and prices of all positions in portfolio.
        Add to portfolio history.
        :param date: Date to update all prices for.
        :param market_data: Market object.
        :return: None.
        """
        for pos in self.position_handler.positions:
            price = market_data.select(columns=[pos],
                                       start_date=date,
                                       end_date=date)
            self.position_handler.positions[pos].update_current_market_price(date=date,
                                                                             market_price=price.iloc[0, 0])
        self.current_date = date
        self.add_history(date=date,
                         market_data=market_data)

        for pos in self.position_handler.positions:
            if self.position_handler.positions[pos].net_quantity == 0:
                del self.position_handler.positions[pos]

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
        self.history.set_index('date',
                               inplace=True)

    def add_history(self,
                    date: str,
                    market_data: Markets) -> None:
        """
        Add portfolio values for a specific date to history.
        :param date: Date to add to portfolio history.
        :param market_data: Market data for benchmark values.
        :return:
        """
        new_bar = []
        if self.benchmark != '':
            bm_value = market_data.select(columns=[self.benchmark],
                                          start_date=self.current_date,
                                          end_date=self.current_date).iloc[0, 0]
            new_bar = [self.current_cash,
                       self.total_commission,
                       self.total_realized_pnl,
                       self.total_unrealized_pnl,
                       self.total_pnl,
                       self.total_market_value,
                       bm_value]
        else:
            new_bar = [self.current_cash,
                       self.total_commission,
                       self.total_realized_pnl,
                       self.total_unrealized_pnl,
                       self.total_pnl,
                       self.total_market_value,
                       0]
        self.history.loc[date] = new_bar

    def crete_records_table(self) -> None:
        """
        Create a holder for all transactions.
        :return: None.
        """
        self.records = pd.DataFrame(columns=['date',
                                             'direction',
                                             'name',
                                             'quantity',
                                             'price',
                                             'commission'])
        self.records.set_index(['date'])

    def add_record(self,
                   t: Transaction) -> None:
        """
        Add a transaction to records.
        :param t: Transaction object.
        :return: None.
        """
        new_record = [t.date,
                      t.direction,
                      t.name,
                      t.quantity,
                      t.price,
                      t.commission]
        self.records.loc[len(self.records)] = new_record


    def transact_security(self,
                          trans: Transaction) -> None:
        """
        Complete buy/sell operation in portfolio given a transaction.
        Add transaction to records.
        :param trans: Transaction object.
        :return: None.
        """
        trans_sec_cost = trans.price * trans.quantity
        trans_total_cost = trans_sec_cost + trans.commission

        if trans_total_cost > self.current_cash:
            print('WARNING: Transaction total cost is larger than current cash.'
                  'Proceeding with negative cash balance.')
        self.position_handler.transact_position(trans=trans)
        if trans.direction == 'B':
            self.current_cash -= trans_total_cost
        else:
            self.current_cash += trans_total_cost

        self.add_record(t=trans)

    @property
    def market_value(self) -> float:
        """
        Calculate the market value of all positions, excluding cash.
        :return: Market value.
        """
        return self.position_handler.total_market_value()

    @property
    def total_market_value(self) -> float:
        """
        Calculate the market value of all positions, including cash.
        :return: Market value.
        """
        return self.position_handler.total_market_value() + self.current_cash

    @property
    def total_pnl(self) -> float:
        """
        Calculate total PnL.
        :return: Total PnL.
        """
        return self.position_handler.total_pnl()

    @property
    def total_realized_pnl(self) -> float:
        """
        Calculate total realized PnL.
        :return: Realized PnL.
        """
        return self.position_handler.total_realized_pnl()

    @property
    def total_unrealized_pnl(self) -> float:
        """
        Calculate total unrealized PnL.
        :return: Unrealized PnL.
        """
        return self.position_handler.total_unrealized_pnl()

    @property
    def total_commission(self) -> float:
        """
        Calculate total commission.
        :return: Total commission.
        """
        return self.position_handler.total_commission()
