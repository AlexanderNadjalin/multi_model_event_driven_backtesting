import abc
import pandas as pd
from holdings.portfolio import Portfolio, Transaction as t
from event_handler.event import Transaction


class Strategy(metaclass=abc.ABCMeta):
    """
    Abstract base class including an event and the date index for which to calculate a signal.
    """
    @abc.abstractmethod
    def calc_signal(self,
                    events,
                    data,
                    idx: str,
                    pf: Portfolio,
                    commission: str):
        pass

    @abc.abstractmethod
    def description(self):
        pass


class BuyAndHold(Strategy):
    def __init__(self,
                 id_num_shares: dict):
        self.pf = None
        self.name = 'Buy and hold'
        self.id_num_shares = id_num_shares
        self.completed = False

    def calc_signal(self,
                    events,
                    data: pd.DataFrame,
                    idx: str,
                    pf: Portfolio,
                    commission: str) -> None:
        if not self.completed:
            self.pf = pf
            for key, item in self.id_num_shares.items():
                intraday_price_col_index = data.columns.get_loc(key)
                intraday_price = data[key].values
                date = pf.current_date
                quantity = int(item)
                trans = t(name=key,
                          direction='B',
                          quantity=quantity,
                          price=intraday_price[0],
                          commission_scheme=commission,
                          date=date)
                trans_ev = Transaction(date=pf.current_date,
                                       trans=trans)
                events.put(item=trans_ev)
                self.completed = True
        else:
            pass

    def description(self) -> str:
        """

        Get {position name: number of shares} as string with line break in between.
        :return: String.
        """
        desc_str = 'Buy-and-hold:' + '\n\n'
        for key, item in self.id_num_shares.items():
            desc_str = desc_str + key + ': ' + str(100 * int(item)) + ' %' + '\n\n'
        return desc_str


class PeriodicRebalancing(Strategy):
    """

    Re-balance the portfolio on either:
    * end-of-month (eom)
    * start-of-month (som)
    * end-of-week (eow)
    * start-of-week (sow)
    Last business day counts as last day of month.
    """
    def __init__(self,
                 period: str,
                 id_weight: dict):
        """

        Set parameters for
        :param period: Either: end-of-month (eom), start-of-month (som), end-of-week (eow) or
        start-of-week (sow).
        :param id_weight: Dictionary with {position name: weight}. Weight between 0 ans 1.0.
        """
        self.pf = None
        if period in ['som', 'eom', 'sow', 'eow']:
            if period == 'sow':
                p = 'start-of-week'
            elif period == 'eow':
                p = 'end-of-week'
            elif period == 'som':
                p = 'start-of-month'
            else:
                p = 'end-of-month'
            self.name = 'Periodic re-balancing'
            self.p = p
            self.period = period
            self.id_weight = id_weight

        else:
            print('CRITICAL: PeriodicRebalancing strategy given parameter period = "'
                  + period + '". Should be either "som", "eom", "sow" or "eow". Aborted.')
            quit()

    def calc_signal(self,
                    events,
                    data: pd.DataFrame,
                    idx: str,
                    pf: Portfolio,
                    commission: str) -> None:
        """

        Calculate if we need to buy more or sell to match target weight.
        :param events: Event queue.
        :param data: Market data from Backtest.
        :param idx: Index from date in Backtest.
        :param pf: Portfolio from Backtest.
        :return: None.
        """
        self.pf = pf
        for key, item in self.id_weight.items():
            positions = self.pf.position_handler.positions

            # No positions in portfolio. Buy to match target weight.
            if not list(positions.items()):
                price = data[key].iloc[0]
                date = pf.current_date
                quantity = int(item * self.pf.total_market_value / price)
                trans = t(name=key,
                          direction='B',
                          quantity=quantity,
                          price=price,
                          commission_scheme=commission,
                          date=date)
                trans_ev = Transaction(date=pf.current_date,
                                       trans=trans)
                events.put(item=trans_ev)

            # Existing positions. Buy or sell to match target weight.
            else:
                pos_mv = pf.position_handler.positions[key].market_value
                pf_mv = pf.total_market_value
                pos_weight = pos_mv / pf_mv
                diff = pos_weight - item

                price = data[key].iloc[0]
                date = pf.current_date

                quantity = int(diff * pf_mv / price)

                if quantity > 0:

                    # Sell excess weight.
                    trans = t(name=key,
                              direction='S',
                              quantity=quantity,
                              price=price,
                              commission_scheme=commission,
                              date=date)
                else:

                    # Buy the difference in weight.
                    trans = t(name=key,
                              direction='B',
                              quantity=quantity * -1,
                              price=price,
                              commission_scheme=commission,
                              date=date)
                trans_ev = Transaction(date=pf.current_date,
                                       trans=trans)
                events.put(item=trans_ev)

    def description(self) -> str:
        """

        Get {position name: weight} as string with line break in between.
        :return: String.
        """
        p = ''
        if self.period in ['som', 'eom', 'sow', 'eow']:
            if self.period == 'sow':
                p = 'start-of-week'
            elif self.period == 'eow':
                p = 'end-of-week'
            elif self.period == 'som':
                p = 'start-of-month'
            else:
                p = 'end-of-month'
        desc_str = 'Periodic re-balancing at ' + p + ':' + '\n\n'
        for key, item in self.id_weight.items():
            desc_str = desc_str + key + ': ' + str(100 * float(item)) + ' %' + '\n\n'
        return desc_str
