import matplotlib.pyplot as plt
from scipy.stats import laplace
import numpy as np
from sympy import Symbol, exp, sqrt, pi, Integral
import math

def laprnd(loc,scale):
    s = laplace.rvs(loc, scale, None)
    return s
