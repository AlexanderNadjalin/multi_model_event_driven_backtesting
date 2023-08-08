import configparser as cp
from event_handler import e_handler, event
from market.markets import Markets
from holdings.portfolio_master import MasterPortfolio
from metric.metric import Metrics


class Backtests:
    """
    Main backtest class.
    Holds a MasterPortfolio, a Market and Metric object.
    """
    def __init__(self,
                 market: Markets,
                 mpf: MasterPortfolio,
                 start_date: str,
                 end_date: str,
                 verbose=False):
        self.config = self.config()

        self.event_handler = e_handler.EventHandler()
        self.current_event = None

        self.cont_backtest = True
        self.market = market
        self.mpf = mpf

        self.verbose = verbose
        self.metric = Metrics()
        self.strategy = None

        self.start_date = start_date
        self.end_date = end_date
        self.validate_date(date=self.start_date)
        self.validate_date(date=self.end_date)
        self.start_index = self.market.data.index.get_loc(self.start_date)

        self.end_index = self.market.data.index.get_loc(self.end_date)

        self.current_date = self.start_date
        self.current_index = self.start_index

    @staticmethod
    def config() -> cp.ConfigParser:
        """
        Read backtest_config file and return a config object. Used to set default parameters for backtesting objects.
        :return: A ConfigParser object.
        """
        conf = cp.ConfigParser()
        conf.read('backtest/backtest_config.ini')

        print('')
        print('INFO: Read from backtest_config.ini file.')

        return conf

    def validate_date(self,
                      date: str) -> bool:
        """
        Check if given date exists in market data.
        :param date: Start or end date.
        :return: True/False.
        """
        if date in self.market.data.index.values:
            return True
        else:
            print('CRITICAL: Date ' + date + ' does not exist in market data files. Aborted.')
            quit()

    def run(self) -> None:
        """
        Runs the backtest for all portfolios as an infinite outer loop for handling dates,
        and an inner loop for handling events.
        :return: None.
        """
        print('INFO: Backtest running from ' + self.start_date + ' to ' + self.end_date + '.')
        print('')
        if self.verbose:
            print('INFO: Verbose logging of events.')

        # Infinite outer loop for handling each date in backtest period
        while self.cont_backtest:
            market_ev = event.NewBar(date=self.current_date,
                                     pf_id='')
            self.event_handler.put_event(market_ev)

            # Infinite inner loop for handling events in event queue.
            while not self.event_handler.is_empty():
                # Handle each event for one portfolio at a time.
                self.current_event = self.event_handler.get_event()

                if self.verbose:
                    print('  ' + self.current_event.details)

                # BAR type event.
                # Done for all portfolios.
                if self.current_event.type == 'BAR':
                    for pf_id in self.mpf.portfolios:
                        # If there is a strategy, calculate signal for it.
                        calc_signal_ev = event.CalcSignal(date=self.current_date,
                                                          pf_id=pf_id)
                        self.event_handler.put_event(event=calc_signal_ev)
                        # Update market values.
                        pf = self.mpf.portfolios.get(pf_id)
                        pf.update_all_market_values(date=self.current_event.date,
                                                    market_data=self.market)
                    self.mpf.update_bench_mark(date=self.current_date,
                                               market=self.market)

                # CALCSIGNAL type event.
                # Done for all portfolios.
                if self.current_event.type == 'CALCSIGNAL':
                    for pf_id in self.mpf.portfolios:
                        pf = self.mpf.portfolios.get(pf_id)
                        # Choose corresponding strategy for the portfolio.
                        self.strategy = self.mpf.strategies.get(pf_id)
                        # Different strategies require different ways to handle calculation of signals.
                        if self.strategy.name == 'Periodic re-balancing':
                            # Get market data for specific date.
                            cols = list(self.strategy.id_weight.keys())
                            df = self.market.select(columns=cols,
                                                    start_date=self.current_event.date,
                                                    end_date=self.current_event.date)
                            transaction = ''
                            # Start-of-month re-balance.
                            if df['is_som'].iloc[0] == 1 and self.strategy.period == 'som':
                                transaction = self.strategy.calc_signal(events=self.current_event,
                                                                        data=df,
                                                                        idx=self.current_index,
                                                                        pf=pf)
                            # End-of-month re-balance.
                            elif df['is_eom'].iloc[0] == 1 and self.strategy.period == 'eom':
                                transaction = self.strategy.calc_signal(events=self.current_event,
                                                                        data=df,
                                                                        idx=self.current_index,
                                                                        pf=pf)
                            # Start-of-week re-balance.
                            elif df['is_sow'].iloc[0] == 1 and self.strategy.period == 'sow':
                                transaction = self.strategy.calc_signal(events=self.current_event,
                                                                        data=df,
                                                                        idx=self.current_index,
                                                                        pf=pf)
                            # End-of-week re-balance.
                            elif df['is_eow'].iloc[0] == 1 and self.strategy.period == 'eow':
                                transaction = self.strategy.calc_signal(events=self.current_event,
                                                                        data=df,
                                                                        idx=self.current_index,
                                                                        pf=pf)
                            # Add transaction from signal generation to event_handler.
                            if transaction:
                                self.event_handler.put_event(event=transaction)

                        elif self.strategy.name == 'Buy and hold':
                            # Get market data for specific date.
                            cols = list(self.strategy.id_num_shares.keys())

                            df = self.market.select(columns=cols,
                                                    start_date=self.current_event.date,
                                                    end_date=self.current_event.date)
                            transaction = self.strategy.calc_signal(data=df,
                                                                    idx=self.current_index,
                                                                    pf=pf,
                                                                    commission=self.mpf.commission)
                            # Add transaction from signal generation to event_handler.
                            if transaction:
                                self.event_handler.put_event(event=transaction)

                        else:
                            pass

                # TRANSACTION type event.
                # Done for a specific portfolio.
                if self.current_event.type == 'TRANSACTION':
                    # Choose the corresponding portfolio.
                    pf = self.mpf.portfolios.get(self.current_event.pf_id)
                    pf.transact_security(trans=self.current_event.trans)

            # Move to next date.
            self.current_index += 1

            # End backtest when end_date is reached.
            if self.current_index > self.end_index:
                # Calculate metrics for all portfolios and for the Master Portfolio.
                for pf_id in self.mpf.portfolios:
                    pf = self.mpf.portfolios.get(pf_id)
                    if not pf.history.empty:
                        self.metric.all_metrics(pf)
                    else:
                        print('WARNING: No transactions made in portfolio ' + pf.pf_id + '.')
                self.metric.all_metrics(self.mpf)
                self.cont_backtest = False
                print('')
                print('SUCCESS: Backtest completed for master portfolio: ' + self.mpf.pf_id + '.')
            else:
                self.current_date = \
                    self.market.data.iloc[self.current_index, :].to_frame().transpose().index.values[0]
                self.mpf.current_date = self.current_date
