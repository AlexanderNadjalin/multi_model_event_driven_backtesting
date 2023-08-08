import datetime as dt
import holdings.commission_scheme as cs


class Transaction:
    """

    Transaction object. One or more transactions together make up a Position object.
    """
    def __init__(self,
                 name: str,
                 direction: str,
                 quantity: float,
                 price: float,
                 commission_scheme: str,
                 date: str):
        """
        :param name: Security identifier (RIC, ticker, ISIN, id etc.)
        :param direction: "B" for bought or "S" for sold.
        :param quantity: Number of units in the transaction. Sign is ignored and handled by direction parameter.
        :param price: Transaction price.
        :param commission_scheme: Name of commission scheme.
        :param date: Transaction date in format "YYYY-MM-DD". Used for history.
        """
        self.name = name
        self.direction = self.validate_direction(direction)
        self.quantity = quantity
        self.price = price
        self.commission_scheme = cs.CommissionScheme(commission_scheme)
        self.commission = self.commission_scheme.calculate_commission(quantity=abs(self.quantity),
                                                                      price=self.price)
        self.date = self.validate_date_format(date)
        self.total_cash = self.commission + abs(self.quantity * self.price)

    @staticmethod
    def validate_date_format(date: str) -> str:
        """
        Make sure date formatting is 'YYYY-MM-DD'.
        :param date: Date.
        :return: Date string.
        """
        try:
            dt.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            print('CRITICAL: Transaction date format must be "YYYY-MM-DD". "' + date + '" was given. Aborted.')
            quit()
        return date

    @staticmethod
    def validate_direction(direction: str) -> str:
        """
        Make sure buy/sell direction is either 'B' or 'S'.
        :param direction: Direction.
        :return: Direction.
        """
        if direction not in ['B', 'S']:
            print('CRITICAL: Transaction direction must be "B" or "S". "' + direction + '" was given. Aborted.')
            quit()
        else:
            return direction
