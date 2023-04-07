import queue
import event as ev


class EventHandler:
    """

    Class for handling events.
    """
    def __init__(self,
                 bt,
                 verbose=False):
        """

        Create empty queue.
        :param bt: Backtest object.
        :param verbose: Bool.
        """
        self.event_queue = queue.Queue()
        self.bt = bt
        self.verbose = verbose

    def put_event(self,
                  event: ev) -> None:
        """

        Put an event in the queue.
        :param event: Event object.
        :return: None.
        """
        self.event_queue.put(event)

    def get_event(self) -> ev:

        """

        Get and remove next event from the queue.
        :return: None.
        """
        return self.event_queue.get()

    def is_empty(self) -> bool:
        """

        Check if queue is empty.
        :return: Bool.
        """
        return self.event_queue.empty()

    def handle_event(self) -> None:
        """

        Decide what to do with an event from the queue.
        :return: None.
        """
        # Get and remove next event from queue.
        e = self.get_event()

        # New market data, new day.
        if e.type == 'BAR':
            # Update market values.
            self.bt.pf.update_all_market_values(date=e.date,
                                                market_data=self.bt.market)
            if self.verbose:
                print('INFO: ' + e.details)

        # See if there is a trade signal.
        if e.type == 'CALCSIGNAL':
            # TODO Complete and add risk handling.
            # TODO Complete and add re-balancing.
            df = self.bt.market.select(columns=self.bt.pf.symbols,
                                       start_date=e.date,
                                       end_date=e.date)

        if self.verbose:
            print('INFO: ' + e.details)

        # Transaction in portfolio.
        elif e.type == 'TRANSACTION':
            self.bt.pf.transact_security(trans=e.trans)
            if self.verbose:
                print('INFO: ' + e.details)
