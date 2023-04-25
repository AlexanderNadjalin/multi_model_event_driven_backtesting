import pandas as pd
import numpy as np
import configparser as cp
from typing import Union
from holdings.portfolio import Portfolio
from holdings.portfolio_master import MasterPortfolio


class Metric:
    """
    Metric object.
    Calculates portfolio metrics for performance, risk, returns etc.
    """
    def __init__(self):
        self.config = self.config()
        self.rolling_beta_period = self.config['rolling_sharpe_ratio']['period']
        self.rolling_sharpe_ratio_period = self.config['rolling_sharpe_ratio']['period']
        self.sharpe_ratio_period = self.config['sharpe_ratio']['period']
        self.sortino_ratio_period = self.config['sortino_ratio']['period']

    def config(self) -> cp.ConfigParser:
        """
        Read metric_config file and return a config object. Used to set default parameters for metric calculations.
        :return: A ConfigParser object.
        """
        conf = cp.ConfigParser()
        conf.read('metric/metric_config.ini')

        print('INFO: Read from metric_config.ini file.')
        print(' ')

        return conf

    @staticmethod
    def returns(pf: Portfolio):
        """
        Add columns for returns of portfolio (pf) and benchmark (bm).
        :param pf: Portfolio for which to calculate returns.
        :return: None.
        """
        pf.metrics = pf.history.copy()
        pf.metrics['pf_1d_pct_rets'] = pf.metrics['total_market_value'].pct_change()
        col_idx = pf.metrics.columns.get_loc('pf_1d_pct_rets')
        pf.metrics.iloc[0, col_idx] = pf.metrics['total_market_value'].iloc[0] / pf.init_cash - 1
        pf.metrics['pf_cum_rets'] = np.cumprod(1 + pf.metrics['pf_1d_pct_rets']) - 1

        # If benchmark exists
        if pf.benchmark == '':
            pass
        else:
            pf.metrics['bm_1d_pct_rets'] = pf.metrics['benchmark_value'].pct_change()
            col_idx = pf.metrics.columns.get_loc('bm_1d_pct_rets')
            pf.metrics.iloc[0, col_idx] = 0
            pf.metrics['bm_cum_rets'] = np.cumprod(1 + pf.metrics['bm_1d_pct_rets']) - 1
        pf.metrics.set_index('date', inplace=True)
        pf.metrics.fillna(0, inplace=True)
        print('INFO: Metrics calculated for returns.')

    @staticmethod
    def create_drawdowns(pf: Portfolio):
        """
        Calculates drawdown and drawdown duration.
        Maximum drawdown is the largest peak-to-trough drop.
        Maximum drawdown duration is defined as the number of periods over which the maximum drawdown occurs.
        :param pf: Portfolio object.
        :return: None.
        """
        high_water_mark = [0]
        equity_curve = pf.metrics['pf_cum_rets']
        eq_idx = pf.metrics.index
        drawdown = pd.Series([], dtype=pd.StringDtype())
        duration = pd.Series([], dtype=pd.StringDtype())

        for t in range(1, len(eq_idx)):
            cur_hwm = max(high_water_mark[t - 1], equity_curve[t])
            high_water_mark.append(cur_hwm)
            if t == 1:
                drawdown[t] = 0
            else:
                if high_water_mark[t] == 0:
                    drawdown[t] = 0
                else:
                    drawdown[t] = (equity_curve[t] / high_water_mark[t] - 1)
            duration[t] = 0 if drawdown[t] == 0 else duration[t - 1] + 1
        pf.metrics['drawdown'] = drawdown
        pf.metrics['duration'] = duration
        pf.metrics['drawdown'].fillna(0, inplace=True)
        pf.metrics['duration'].fillna(0, inplace=True)
        print('INFO: Metrics calculated for drawdowns.')

    @staticmethod
    def max_drawdown(pf: Portfolio) -> float:
        """
        Calculate maximum drawdown in percent.
        Requires that metrics.create_drawdowns() has been run.
        :param pf: Portfolio.
        :return: Maximum drawdown value in percent.
        """
        return pf.metrics['drawdown'].min()

    @staticmethod
    def max_drawdown_duration(pf: Portfolio) -> float:
        """
        Calculate maximum drawdown duration in days.
        Requires that metrics.create_drawdowns() has been run.
        :param pf: Portfolio.
        :return: Maximum drawdown duration in days.
        """
        return pf.metrics['duration'].max()

    def create_rolling_sharpe_ratio(self,
                                    pf: Portfolio) -> None:
        """
        Calculates the 6m Sharpe ratio for the strategy and the benchmark.
        :param pf: Portfolio object.
        :return: None.
        """
        period = int(self.config['rolling_sharpe_ratio']['period'])
        if len(pf.metrics.index) < period:
            data_len = len(pf.metrics.index)
            print('WARNING: Chosen backtesting period has ' + str(data_len) +
                  ' data points. Rolling Sharpe ratio needs ' + str(period) +
                  ' data points. Adjust backtesting dates or period parameter in backtest_config.ini')
        else:
            # equity TimeSeries only
            eq_rets = pf.metrics['pf_1d_pct_rets']
            eq_rolling = eq_rets.rolling(window=period)
            eq_rolling_sharpe = np.sqrt(period) * eq_rolling.mean() / eq_rolling.std()
            eq_rolling_sharpe.fillna(0, inplace=True)
            pf.metrics['pf_sharpe_ratio'] = eq_rolling_sharpe

            # benchmark TimeSeries included
            if pf.benchmark != '':
                bm_rets = pf.metrics['bm_1d_pct_rets']
                bm_rolling = bm_rets.rolling(window=period)
                bm_rolling_sharpe = np.sqrt(period) * bm_rolling.mean() / bm_rolling.std()
                bm_rolling_sharpe.fillna(0, inplace=True)
                pf.metrics['bm_sharpe_ratio'] = bm_rolling_sharpe
                print('INFO: Metrics calculated for rolling Sharpe ratio.')
            else:
                print('WARNING: No benchmark selected for portfolio ' + pf.pf_id +
                      '. Rolling Sharpe ratio not calculated.')

        pf.metrics.fillna(0, inplace=True)

    def create_rolling_beta(self,
                            pf: Portfolio) -> None:
        """
        Rolling beta.
        :param pf: Portfolio object.
        :return: None.
        """
        period = int(self.config['rolling_beta']['period'])
        if len(pf.metrics.index) < period:
            data_len = len(pf.metrics.index)
            print('WARNING: Chosen backtesting period has ' + str(data_len) +
                  ' data points. Rolling beta needs ' + str(period) +
                  ' data points. Adjust backtesting dates or period parameter in backtest_config.ini')
        else:
            if pf.benchmark != '':
                pf_idx = pf.metrics.columns.get_loc('pf_1d_pct_rets')
                bm_idx = pf.metrics.columns.get_loc('bm_1d_pct_rets')
                pf_ = pf.metrics.iloc[:, pf_idx]
                bm_ = pf.metrics.iloc[:, bm_idx]
                roll_pf = pf_.rolling(window=period)
                roll_bm = bm_.rolling(window=period)
                roll_var = roll_pf.var()
                roll_cov = roll_pf.cov(roll_bm)

                # Periods longer than "period" of no variance makes for division by zero. Floor to low non-zero value.
                roll_var = roll_var.apply(lambda x: x if x > 1.e-05 else 0.00001)
                rolling_beta = roll_cov / roll_var
                rolling_beta.dropna(inplace=True)
                pf.metrics['rolling_beta'] = rolling_beta

                pf.metrics.fillna(0, inplace=True)

                print('INFO: Metrics calculated for rolling beta.')
            else:
                print('WARNING: No benchmark selected for portfolio ' + pf.pf_id + '. Rolling beta not calculated.')

    def all_metrics(self,
                    pf: Union[Portfolio, MasterPortfolio]) -> None:
        """
        Calculate all metrics.
        :param pf: Portfolio object or a MasterPortfolio object.
        :return: None.
        """
        self.returns(pf=pf)
        self.create_drawdowns(pf=pf)
        self.create_rolling_sharpe_ratio(pf=pf)
        self.create_rolling_beta(pf=pf)
        self.cagr(pf=pf)
        self.sortino_ratio(pf=pf)

    def cagr(self,
             pf: Portfolio) -> float:
        """
        Calculate the Compound Annual Growth Rate (CAGR) as:
        (Value(start) / Value(end)) ^ (1 / time) - 1
        :return: CAGR value in percent.
        """
        time = 1 / len(pf.metrics)
        cagr = (pf.metrics['total_market_value'].iloc[-1] / pf.metrics['total_market_value'].iloc[0]) ** time - 1.0
        return cagr * 100

    def sharpe_ratio(self,
                     pf: Portfolio) -> float:
        """
        Calculate Sharpe ratio for a Portfolio that has been used in a Backtest.
        Requires that metrics.calc_returns() has been run.
        Period is set in the metrics.metrics_config.ini file.
        :param pf: Portfolio object.
        :return: Sharpe ratio.
        """
        # Get data from backtest results.
        df = pf.metrics.copy()
        df['dt'] = pd.to_datetime(df.index,
                                  format='%Y-%m-%d')
        df.reset_index(inplace=True)
        df.set_index(keys='dt',
                     inplace=True)

        rets = df['pf_1d_pct_rets']

        return np.sqrt(float(self.sharpe_ratio_period)) * (np.mean(rets)) / np.std(rets)

    def sortino_ratio(self,
                      pf: Portfolio) -> float:
        """
        Calculate Sortino ratio for portfolio.
        :param pf:Portfolio object.
        :return: Sortino ratio.
        """
        # Get data from backtest results.
        df = pf.metrics.copy()
        df['dt'] = pd.to_datetime(df.index,
                                  format='%Y-%m-%d')
        df.reset_index(inplace=True)
        df.set_index(keys='dt',
                     inplace=True)

        rets = df['pf_1d_pct_rets']

        return np.sqrt(float(self.sortino_ratio_period)) * (np.mean(rets)) / np.std(rets[rets < 0])

    def tot_pf_rets(self,
                    pf: Portfolio) -> float:
        """
        Get total returns for portfolio in backtest.
        :param pf: Portfolio object.
        :return: Portfolio returns in decimal format.
        """
        # Get data from backtest results.
        p1 = pf.metrics.columns.get_loc('pf_cum_rets')
        pf_cum_rets_pct = pf.metrics.iloc[:, p1]

        return pf_cum_rets_pct.iloc[-1]

    def tot_bm_rets(self,
                    pf: Portfolio) -> float:
        """
        Get total returns for benchmark in backtest.
        :param pf: Portfolio object.
        :return: Benchmark returns in decimal format.
        """
        if pf.benchmark is None:
            print('CRITICAL: No benchmark for portfolio. Check portfolio_config.ini file. Aborted.')
            quit()
        # Get data from backtest results.
        p1 = pf.metrics.columns.get_loc('bm_cum_rets')
        pf_cum_rets_pct = pf.metrics.iloc[:, p1]

        return pf_cum_rets_pct.iloc[-1]
