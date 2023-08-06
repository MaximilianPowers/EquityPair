import numpy as np

def safe_round(number, d=2):
    if number is not None:
        if np.isnan(number):
            return np.nan
        else:
            return np.round(number, d)
    else:
        return 0