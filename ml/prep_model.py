# This file contains functions for saving and loading a trained model.
import os
from keras.models import load_model, save_model
import ml.DNN as DNN


def save_load_model(save: bool,
                    model_file_name: str,
                    model: None) -> None or DNN:
    """

    Load/save an agent from/to file.

    If save (requires a trained agent and model):
        - Save one file for the agent object (tradingbot.TradingBot) as a pickled .pkl file.
        - Save one file for the agents model attribute using Tensorflow.Keras module as .h5 file.
    If load (saves time to not train the model every run):
        - Load a saved agent object and corresponding model file.
    """
    os.chdir(model_file_name)

    if not save:
        with open(model_file_name, 'rb') as infile:
            model = load_model(infile)
            print('')
            print('Model file loaded.')
        return model
    else:
        save_model(model=model,
                   filepath=model_file_name,
                   overwrite=True)
        print('Model file saved.')
