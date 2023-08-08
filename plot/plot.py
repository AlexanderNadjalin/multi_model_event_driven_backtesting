import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from backtest.backtest import Backtests
from holdings.portfolio import Portfolio


class Plot:
    """
    Plot object to visualize different metrics.
    Requires that Metric.calc_all() method has been run.
    """

    def __init__(self,
                 bt: Backtests):
        self.bt = bt

    def strategy_name(self,
                      pf: Portfolio) -> str:
        return self.bt.mpf.strategies.get(pf)

    def strategy_period(self,
                        pf: Portfolio) -> str:
        return self.bt.mpf.strategies.get(pf)

    def rolling_sharpe_beta_plot(self,
                                 pf_list: list,
                                 save=False) -> plt.figure():
        """
        Dual plot with rolling Sharpe ratio above, and rolling beta below.
        :param pf_list: List with Portfolio and/or MasterPortfolio objects.
        :param save: True ito save to file.
        :return: Matplotlib figure.
        """
        for item in pf_list:
            try:
                p1 = item.metrics.columns.get_loc('pf_sharpe_ratio')
                p2 = item.metrics.columns.get_loc('rolling_beta')
            except:
                print('WARNING: No metrics exist for Sharpe Ratio or Beta. Backtesting window too short.')
                print('WARNING: No plot created.')
                return
            fig, axes = plt.subplots(2, 1, figsize=(10, 7))
            ax1 = plt.subplot(211)
            ax2 = plt.subplot(212)

            item.metrics.iloc[:, p1].plot(lw=1, color='black', alpha=0.60, ax=ax1, label='Sharpe ratio')
            item.metrics.iloc[:, p2].plot(lw=1, color='green', alpha=0.60, ax=ax2, label='Beta')

            # Include strategy name in title
            title_sharpe = 'Rolling ' + str(self.bt.mpf.metrics_config['rolling_sharpe_ratio']['period']) \
                           + ' days Sharpe ratio'
            title_beta = 'Rolling ' + str(self.bt.mpf.metrics_config['rolling_beta']['period']) + ' days Beta'

            title_strat = ''
            if isinstance(item, Portfolio):
                # MasterPortfolio object has just a dict for holding strategies of Portfolios.
                title_strat = self.bt.mpf.strategies.get(item.pf_id).name
            # Is MasterPortfolio object.
            else:
                title_strat = 'Master Portfolio.'
            ax1.set_title(title_sharpe + '\n' + title_strat)

            ax1.set_xlabel('Date')
            self.plot_look(ax=ax1,
                           look_nr=1)

            ax2.set_title(title_beta)
            self.plot_look(ax=ax2,
                           look_nr=1)

            fig.tight_layout()

            if save:
                self.save_plot(name=self.bt.config['output_files']['output_file_directory'] +
                                    '_rolling_sharpe_beta.png',
                               fig=fig)
            plt.show()

    def drawdowns_plot(self,
                       pf_list: list,
                       save=False) -> plt.figure():
        """
        Dual plot with cumulative portfolio returns and benchmark returns above, and drawdowns below.
        Includes portfolio and benchmark returns of ver backtest period, and maximum drawdown duration.
        :param pf_list: List with Portfolio and/or MasterPortfolio objects.
        :param save: True to save to file.
        :return: None
        """
        for item in pf_list:
            p1 = item.metrics.columns.get_loc('pf_cum_rets')
            p2 = item.metrics.columns.get_loc('bm_cum_rets')
            p3 = item.metrics.columns.get_loc('drawdown')

            title_dd = 'Drawdowns (maximum duration: ' + str(int(item.metrics['duration'].max())) + ' days)'

            fig, axes = plt.subplots(2, 1, figsize=(10, 7))
            ax1 = plt.subplot(211)
            ax2 = plt.subplot(212)

            pf_cum_rets_pct = item.metrics.iloc[:, p1] * 100
            bm_cum_rets_pct = item.metrics.iloc[:, p2] * 100
            dd_pct = item.metrics.iloc[:, p3]

            pf_cum_rets_pct.plot(lw=1, color='black', alpha=0.60, ax=ax1, label='Portfolio')
            bm_cum_rets_pct.plot(lw=1, color='green', alpha=0.60, ax=ax1, label='Benchmark')
            dd_pct.plot(lw=1, color='black', alpha=0.60, ax=ax2, label='Drawdowns')

            ax1.set_xlabel('Date')
            ax1.set_ylabel('%')
            pf_tot_rets = str(format(pf_cum_rets_pct.iloc[-1], ".2f"))
            bm_tot_rets = str(format(bm_cum_rets_pct.iloc[-1], ".2f"))

            title_strat = ''
            title_str = 'Cumulative returns (Portfolio: ' + pf_tot_rets + '%, Benchmark: ' + bm_tot_rets + '%)'
            # Include strategy name in title.
            if isinstance(item, Portfolio):
                title_strat = 'Strategy: ' + self.bt.mpf.strategies.get(item.pf_id).name
            else:
                title_strat = 'Master Portfolio'
            ax1.set_title(title_str + '\n' + title_strat)

            self.plot_look(ax=ax1,
                           look_nr=1)

            ax2.set_xlabel('Date')
            ax2.set_ylabel('%')
            ax2.set_title(title_dd)
            self.plot_look(ax=ax2,
                           look_nr=1)

            fig.tight_layout()

            if save:
                self.save_plot(name=self.bt.config['output_files']['output_file_directory'] + '_drawdowns.png',
                               fig=fig)
            plt.show()

    @staticmethod
    def plot_look(ax: plt.subplots,
                  look_nr: int):
        """
        Set plot look.
        :param ax: Matplotlib ax object.
        :param look_nr: Desired look as number. More to be implemented.
        :return:
        """
        if look_nr == 1:
            ax.minorticks_on()
            ax.grid(visible=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
            ax.grid(visible=True, which='major', color='#999999', linestyle='-', alpha=0.4)
            ax.legend(loc='best', prop={'size': 8})
            plt.setp(ax.get_xticklabels(), visible=True, rotation=45, ha='center')
        else:
            print('WARNING: Plot look number ' + str(look_nr) + ' is not implemented.')

    def aggr_rets(self,
                  rets: pd.DataFrame,
                  period: str) -> np.array:
        """
        Convert daily returns to aggregated returns per given period - yearly, monthly and weekly.
        :param rets: Market data from Backtest.
        :param period:
        :return: Numpy array with converted returns.
        """
        def cumulate_rets(x):
            return np.exp(np.log(1 + x).cumsum())[-1] - 1

        if period == 'weekly':
            return rets.groupby(
                [lambda x: x.year,
                 lambda x: x.isocalendar()[1]]).apply(cumulate_rets) * 100
        elif period == 'monthly':
            return rets.groupby(
                [lambda x: x.year, lambda x: x.month]).apply(cumulate_rets) * 100
        elif period == 'yearly':
            return rets.groupby(
                [lambda x: x.year]).apply(cumulate_rets) * 100
        else:
            print('CRITICAL: Chosen aggregated period "' + period + '" is not implemented. Aborted.')
            quit()

    def save_plot(self,
                  name: str,
                  fig) -> None:
        """
        Save file as .png in /output_files directory.
        :param name: File name.
        :param fig: Figure to be saved.
        :return: None.
        """
        try:
            fig.figure.savefig(name,
                               bbox_inches='tight')
            print('SUCCESS: Plot saved at: ' + name + '.')
        except FileNotFoundError:
            print('WARNING: File destination incorrect. Check backtest_config.ini file. Plot not saved.')
