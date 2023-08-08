import holdings.transaction as transaction


class Event:
    """
    Base class for events.
    """


class NewBar(Event):
    """
    Market event indicates that a new day has passed and there is new market data.
    """
    def __init__(self,
                 date: str,
                 pf_id: str):
        self.type = 'BAR'
        self.date = date
        self.pf_id = pf_id

    @property
    def details(self) -> str:
        """
        Details for verbose logging.
        :return: String for logging.
        """
        return f'{self.date} - Portfolio: {self.pf_id} - Event: BAR.'

    @property
    def event_type(self) -> str:
        """
        Event type.
        :return: Event type.
        """
        return self.type


class Transaction(Event):
    """
    Transaction (buy or sell) event for a position in a portfolio.
    """
    def __init__(self,
                 date: str,
                 trans: transaction.Transaction,
                 pf_id: str):
        self.type = 'TRANSACTION'
        self.date = date
        self.trans = trans
        self.pf_id = pf_id

    @property
    def details(self) -> str:
        """
        Details for verbose logging.
        :return: String for logging.
        """
        return f'{self.date} - Portfolio: {self.pf_id} - Event: TRANSACTION. Details: {self.trans.direction} ' \
               f'{self.trans.quantity} {self.trans.name} @ {self.trans.price}'

    @property
    def event_type(self) -> str:
        """
        Event type.
        :return: Event type.
        """
        return self.type


class CalcSignal(Event):
    """
    Event indicating that we need to calculate the Strategy's signal requirements.
    """
    def __init__(self,
                 date: str,
                 pf_id: str):
        self.type = 'CALCSIGNAL'
        self.date = date
        self.port_id = pf_id

    @property
    def details(self) -> str:
        """
        Details for verbose logging.
        :return: String for logging.
        """
        return f'{self.date} - Portfolio: {self.pf_id}. Event: CALCSIGNAL.'

    @property
    def event_type(self) -> str:
        """
        Event type.
        :return: Event type.
        """
        return self.type

    @property
    def pf_id(self) -> str:
        """
        Event type.
        :return: Portfolio id.
        """
        return self.port_id
