import holdings.transaction as transaction


class Event:
    """

    Base class for events.
    """
    pass


class NewBar(Event):
    """

    Market event indicates that a new day has passed and there is new market data.
    """
    def __init__(self,
                 date: str):
        self.type = 'BAR'
        self.date = date
        print(' ')

    @property
    def details(self) -> str:
        """

        Details for verbose logging.
        :return: String for logging.
        """
        return 'New bar event [date: %s]' % self.date


class Transaction(Event):
    """

    Transaction (buy or sell) event for a position in a portfolio.
    """
    def __init__(self,
                 date: str,
                 trans: transaction.Transaction):
        self.type = 'TRANSACTION'
        self.date = date
        self.trans = trans
        print(' ')

    @property
    def details(self) -> str:
        """

        Details for verbose logging.
        :return: String for logging.
        """
        return 'Transaction event [date: %s, direction: %s, name: %s, quantity: %s, price: %s]' % (self.date,
                                                                                                   self.trans.direction,
                                                                                                   self.trans.name,
                                                                                                   self.trans.quantity,
                                                                                                   self.trans.price)


class CalcSignal(Event):
    """

    Event indicating that we need to calculate the Strategy's signal requirements.
    """
    def __init__(self,
                 date: str):
        self.type = 'CALCSIGNAL'
        self.date = date
        print(' ')

    @property
    def details(self) -> str:
        """

        Details for verbose logging.
        :return: String for logging.
        """
        return 'Calculate signal event [date: %s]' % self.date
