import os
import numpy as np
import pandas as pd
from environments import finance
from bots import tradingbot
from backtesters import tbbacktestingrm as tbbtrm
from file_handling import file_handling as fh


# Global options
pd.set_option('mode.chained_assignment', None)
pd.set_option('display.float_format', '{:.4f}'.format)
np.set_printoptions(suppress=True, precision=4)
os.environ['PYTHONHASHSEED'] = '0'

def main(model_file_name, agent_file_name, train=False, episodes=61, save_model=False, save_plots=False):
    # Get config details of file directories
    conf = fh.config()

    # Get symbol, specify features.
    symbol = 'EUR='
    features = [symbol, 'rets', 'spot', 'mean', 'vol', 'rsi_2']
    rsi_params = [14, 2]

    # Learning start bar
    a = 0
    # Learning end bar, validation start bar
    b = 1200
    # Validation end bar, testing start
    c = 1600

    # Trainging environment
    train_env = finance.Finance(symbol, features, rsi_params=rsi_params, window=20, lags=3,
                                leverage=1, min_performance=0.9, min_accuracy=0.475, env_type='training',
                                start=a, end=b, mu=None, std=None)

    # Validation environment
    valid_env = finance.Finance(symbol, features=train_env.features,
                                rsi_params=rsi_params,
                                window=train_env.window,
                                lags=train_env.lags,
                                leverage=train_env.leverage,
                                min_performance=0.0, min_accuracy=0.0, env_type='validation',
                                start=b, end=c,
                                mu=train_env.mu, std=train_env.std)

    # Test environment
    test_env = finance.Finance(symbol, features=train_env.features,
                               rsi_params=rsi_params,
                               window=train_env.window,
                               lags=train_env.lags,
                               leverage=train_env.leverage,
                               min_performance=0.0, min_accuracy=0.0, env_type='test',
                               start=c, end=None,
                               mu=train_env.mu, std=train_env.std)

    agent = None

    if train:
        tradingbot.set_seeds(100)
        agent = tradingbot.TradingBot(24, 0.001, train_env, valid_env)
        agent.learn(episodes)
        if save_model:
            fh.save_load_agent(agent_file_name, model_file_name, save_model, conf)
        else:
            print('Model and agent files will not be saved.')
    else:
        if not save_model:
            agent = fh.save_load_agent(agent_file_name, model_file_name, save_model, conf)
        else:
            print('Can not save a non-trained model. Aborted.')
            quit()

    # Set up backtest
    env = [train_env, valid_env, test_env]
    for e in env:
        tb = tbbtrm.TBBacktesterRM(e, agent.model, 10000, 0.00012, 0, verbose=False)
        print(tb.backtest_strategy(sl=None, tsl=None, tp=None, wait=5))
        # Plot results
        plotting.plot_single_series(tb, in_sample=False, conf=conf, save_fig=save_plots)


if __name__ == '__main__':
    main(model_file_name='model_EUR_USD_rsi.h5',
         agent_file_name='agent_EUR_USD_rsi.pkl',
         train=True,
         episodes=61,
         save_model=False,
         save_plots=True)
