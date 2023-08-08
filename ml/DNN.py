# This file contains the DNN class, which is used to create a Deep Neural Network model.
import configparser as cp
import numpy as np
import pandas as pd
from keras.layers import Dense
from keras.models import Sequential
from keras.optimizers import RMSprop
from ml.prep_model import save_load_model


class DNN:
    def __init__(self,
                 data: pd.DataFrame,
                 load_from_file: bool,
                 model_file_name: str,
                 train: bool,
                 save_trained: False) -> None:
        self.config = self.config()
        self.load_from_file = load_from_file
        self.model_file_name = self.config['models_directory']['models_directory'] + '\\' + model_file_name
        self.train = train
        self.save_trained = save_trained
        self.symbol = self.config['symbol']['symbol']
        self.features = self.config['features']['features']
        self.num_features = len(self.features)
        self.window = int(self.config['parameters']['window'])
        self.rsi_params = list(self.config['parameters']['rsi_params'].split(', '))
        self.lags = self.config['parameters']['lags']
        self.episodes = self.config['parameters']['episodes']
        self.data = data[self.symbol + '_Close'].copy().to_frame()
        self.mu = self.data[self.symbol + '_Close'].mean()
        self.std = self.data[self.symbol + '_Close'].std()
        self.data_norm= (self.data - self.mu) / self.std
        self.data['d'] = np.where(self.data['rets'] > 0, 1, 0)
        self.data['d'] = self.data['d'].astype(int)
        self.min_performance = self.config['parameters']['min_performance']
        self.accuracy = self.config['parameters']['accuracy']
        self.loss = self.config['parameters']['loss']
        self.model = None
        if train:
            self.add_features()
        self.create_model()

    @staticmethod
    def config() -> cp.ConfigParser:
        """
        Read dnn_config file and return a config object. Used to set default parameters for DNN objects.
        :return: A ConfigParser object.
        """
        conf = cp.ConfigParser()
        conf.read('ml/dnn_config.ini')

        print('')
        print('INFO: Read from dnn_config.ini file.')

        return conf

    def add_features(self):
        close_col = self.symbol + '_Close'
        if 'rets' in self.features:
            # Returns
            self.data['rets'] = np.log(self.data[close_col] / self.data[close_col].shift(1))
            self.data.dropna(inplace=True)

        if 'spot' in self.features:
            # Spot
            self.data['spot'] = self.data[close_col].rolling(self.window).mean()

        if 'mean' in self.features:
            # Mean
            self.data['mean'] = self.data['rets'].rolling(self.window).mean()

        if 'vol' in self.features:
            # Volatility
            self.data['vol'] = self.data['rets'].rolling(self.window).std()
            self.data.dropna(inplace=True)

        if 'rsi' in self.features:
            for i in self.rsi_params:
                self.relative_strength_index(window=int(i))

    def relative_strength_index(self,
                                window: int = 14):
        """
        Calculate RSI (Relative Strength Index) with  SMA ("SMA" for
        Simple Moving Average).
        :param window: int: Period for the RSI.
        """

        def rma(x, n, y0):
            a = (n - 1) / n
            ak = a ** np.arange(len(x) - 1, -1, -1)
            return np.append(y0, np.cumsum(ak * x) / ak / n + y0 * a ** np.arange(1, len(x) + 1))

        if 'change' not in self.data.columns:
            self.data['change'] = self.data['spot'].diff()
        if 'gain' not in self.data.columns:
            self.data['gain'] = self.data.change.mask(self.data.change < 0, 0.0)
        if 'loss' not in self.data.columns:
            self.data['loss'] = -self.data.change.mask(self.data.change > 0, -0.0)
        self.data['avg_gain'] = 0
        col_avg_gain = self.data.columns.get_loc("avg_gain")
        col_gain = self.data.columns.get_loc("gain")
        self.data.iloc[window:, col_avg_gain] = rma(self.data.gain[window + 1:].values, window,
                                                    self.data.iloc[:window, col_gain].mean())
        self.data['avg_loss'] = 0
        col_avg_loss = self.data.columns.get_loc("avg_loss")
        col_loss = self.data.columns.get_loc("loss")
        self.data.iloc[window:, col_avg_loss] = rma(self.data.loss[window + 1:].values, window,
                                                    self.data.iloc[:window, col_loss].mean())
        self.data['rs'] = self.data.avg_gain / self.data.avg_loss
        self.data['rsi_' + str(window)] = 100 - (100 / (1 + self.data.rs))

        self.data.drop(['change', 'gain', 'loss', 'avg_gain', 'avg_loss', 'rs'], axis=1, inplace=True)

        self.data.dropna(inplace=True)

    def create_model(self,
                     dropout: bool,
                     hl=1,
                     hu=128) -> None:
        """
        Create a DNN model from either a saved model or a new model.
        :param dropout:
        :param hl:
        :param hu:
        :return:
        """
        if self.load_from_file:
            self.model = save_load_model(save=False,
                                         model_file_name=self.model_file_name,
                                         model=None)
        else:
            model = Sequential()
            # Default layer
            model.add(Dense(hu, input_shape=(self.lags, self.num_features), activation='relu'))
            for _ in range(hl):
                # Additional layer
                model.add(Dense(hu, activation='relu'))
                # Output layer
                model.add(Dense(1, activation='sigmoid'))
                # Loss function
                model.compile(loss='mse', optimizer=RMSprop(), metrics=['accuracy'])
            self.model = model
            if self.train:
                self.train_model()
            if self.save_trained:
                save_load_model(save=True,
                                model_file_name=self.model_file_name,
                                model=None)

    def train_model(self) -> None:
        """
        Train the DNN model.
        :return: None.
        """
        # Train the model
        self.model.fit(self.X_train,
                       self.y_train,
                       epochs=self.episodes,
                       batch_size=self.batch_size,
                       verbose=0)