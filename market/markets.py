import configparser as cp
from pathlib import Path
import pandas as pd


class Markets:
    def __init__(self,
                 fill_missing_method) -> None:
        """

        Markets class object.
        :param fill_missing_method: Fill missing values method as string.
        """
        self.config = self.config()
        self.assets = []
        self.fill_missing_method = fill_missing_method
        self.data = pd.DataFrame()
        self.read_csv()
        self.data_valid()
        self.columns = self.data.columns.to_list()
        self.som_eom()
        print('SUCCESS: Market created.')

    @staticmethod
    def config() -> cp.ConfigParser:
        """

        Read market_config file and return a config object. Used to designate target directories for data and models.
        Config.ini file is located in project base directory.
        :return: A ConfigParser object.
        """
        conf = cp.ConfigParser()
        conf.read('market/market_config.ini')

        print('INFO: I/O info read from market_config.ini file.')

        return conf

    def read_csv(self) -> None:
        """

        Read config.ini file. Read all files in /input_files/assets.
        All files must be of ".csv" type and in Yahoo Finance historical download daily format.
        Merge all files on dates with inner join, leaving the maximum number of dates that are equal.
        :return: None.
        """

        input_file_directory = Path(self.config['input_files']['input_file_directory'])
        num_files = 0

        # Loop over each file in the directory.
        for f in list(input_file_directory.iterdir()):
            # Read file into DataFrame.
            try:
                raw_data = pd.read_csv(f, sep=',')
            except ValueError as e:
                print('ERROR: File read failed with the following exception:')
                print('   ' + str(e))
                print('INFO: Aborted.')
                quit()
            else:
                file_name = str(f.stem)
                self.assets.append(file_name)
                print('INFO: Data file "' + file_name + '" read.')

                # Change column names to include asset name.
                raw_data.rename(columns={'Open': file_name + '_Open',
                                         'High': file_name + 'High',
                                         'Low': file_name + '_Low',
                                         'Close': file_name + '_Close',
                                         'Adj Close': file_name + '_AdjClose',
                                         'Volume': file_name + '_Volume'},
                                inplace=True)
                raw_data = raw_data.set_index(['Date'])

                # For the first file we use the data as is.
                if num_files == 0:
                    self.data = raw_data.copy()
                # For subsequent files we merge on date (inner join).
                else:
                    self.data = pd.merge(self.data,
                                         raw_data,
                                         left_index=True,
                                         right_index=True)
                num_files += 1
        self.data.dropna(inplace=True)

    def data_valid(self) -> None:
        """

        Check for NaN, empty values and non-floats.
        Fill missing values.
        :return: None
        """
        cols = list(self.data.columns)
        empties = 0
        nans = 0
        floats = 0
        for col in cols:
            col_empties = len(self.data[self.data[col] == ''])
            col_nans = self.data[col].isna().sum()
            if self.data[col].dtypes != 'float64':
                floats += 1
            empties += col_empties
            nans += col_nans

            if col_empties > 0:
                print('WARNING: Column ' + col + ' has ' + str(col_empties) + ' number of empty values.')
                self.fill_missing(col_name=col)
            if col_nans > 0:
                print('WARNING: Column ' + col + ' has ' + str(col_nans) + ' number of NaN values.')
            if floats > 0:
                print('WARNING: Column ' + col + ' has one or more non-float values.')

        if (empties == 0) and (nans == 0) and (floats == 0):
            print('INFO: No empty, NaN or non-float values in imported file.')

    def fill_missing(self,
                     col_name) -> None:
        """

        Fill missing values in a column of self.data with given method.
        :param col_name: Column name. Passing "None" does nothing.
        :return: None.
        """
        if self.fill_missing_method == 'forward':
            self.data[col_name].fillna(method='ffill', inplace=True)
            print('INFO: Column ' + col_name + ' forward-filled.')
        elif self.fill_missing_method == 'backward':
            self.data[col_name].fillna(method='bfill', inplace=True)
            print('INFO: Column ' + col_name + ' backward-filled.')
        elif self.fill_missing_method == 'interpolate':
            self.data[col_name].interpolate(method='polynomial')
            print('INFO: Column ' + col_name + ' filled by interpolation.')
        elif self.fill_missing_method is None:
            pass
        else:
            print('CRITICAL: Fill method ' + self.fill_missing_method + ' not implemented. Aborted.')
            quit()

    def som_eom(self) -> None:
        """

        Add columns indicating:
        * is_som -> is-start-of-month
        * is_eom -> is-end-of-month
        * is_sow -> is-start-of-week
        * is_eow -> is-end-ow-week
        Used for monthly re-balancing strategies.
        :return: None.
        """
        # Add temporary columns for month and week.
        self.data['dt'] = pd.to_datetime(self.data.index,
                                         format='%Y-%m-%d')
        self.data['month'] = self.data['dt'].dt.month.diff()
        self.data['month'].fillna(0.0, inplace=True)
        self.data['week'] = self.data['dt'].dt.isocalendar().week.diff()
        self.data['week'].fillna(0.0, inplace=True)

        # Start of month.
        self.data['is_som'] = self.data['month'].apply(lambda x: 1 if x != 0.0 else 0)

        # End of month.
        self.data['is_eom'] = self.data['is_som'].shift(-1)
        self.data['is_eom'].fillna(0.0, inplace=True)
        self.data['is_eom'] = self.data['is_eom'].astype(int)

        # Start of week.
        self.data['is_sow'] = self.data['week'].apply(lambda x: 1 if x != 0.0 else 0)

        # End of week.
        self.data['is_eow'] = self.data['is_sow'].shift(-1)
        self.data['is_eow'].fillna(0.0, inplace=True)
        self.data['is_eow'] = self.data['is_eow'].astype(int)

        # Drop temp columns.
        self.data.drop(labels='month',
                       axis='columns',
                       inplace=True)
        self.data.drop(labels='week',
                       axis='columns',
                       inplace=True)
        self.data.drop(labels='dt',
                       axis='columns',
                       inplace=True)

    def select(self,
               columns: list,
               start_date: str,
               end_date: str) -> pd.DataFrame:
        """

        Select a subset of market data between start_date and end_date.
        :param columns: List of column names.
        :param start_date: Start date (the oldest date, included in selection).
        :param end_date:End date (the newest date, included in selection)
        :return: Pandas dataframe.
        """
        cols = columns.copy()
        if any(item in self.columns for item in columns):
            if start_date not in self.data.index.values:
                print('CRITICAL: Selected start date not in market data. Aborted.')
                quit()
            if end_date not in self.data.index.values:
                print('CRITICAL: Selected end date not in market data. Aborted.')
                quit()
            mask = (self.data.index.values >= start_date) & (self.data.index.values <= end_date)
            cols.append('is_som')
            cols.append('is_eom')
            cols.append('is_sow')
            cols.append('is_eow')
            df = self.data[cols].loc[mask]
            return df
        else:
            print('CRITICAL: Selected column name not in market data. Aborted.')
            quit()

    def date_from_index(self,
                        current_date: str,
                        index_loc: int) -> str:
        """

        Get date as string. Starts at current date and offsets index_loc number of days.
        :param current_date: Date.
        :param index_loc: Number of offset days.
        :return: Date.
        """
        mask = (self.data.index.values >= current_date)
        df = self.data.loc[mask]
        date = df.iloc[[index_loc]].index.values[0]
        return date
