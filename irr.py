import scipy.optimize as opt
import numpy as np
from numpy.typing import ArrayLike
import logging

def irr(cashflow: ArrayLike, guess: float = 0.0)->float:
    def npv(r: float)->float:
        periods = np.arange(len(cashflow))
        return sum(cashflow / (1+r)**periods)
    try:
        r = opt.broyden1(npv, guess, f_tol=1e-10)
    except opt.nonlin.NoConvergence as e:
        r = e.args[0]
        logging.warning("IRR solver doesn't converge!")
    return r