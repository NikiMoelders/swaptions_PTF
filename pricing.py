# ============================================================
# 0) Imports
# ============================================================

import numpy as np
import pandas as pd
from scipy.stats import norm

# ============================================================
# 1) Utilities
# ============================================================

def zero_to_df(z, t):
    """
    Converts a simply-compounded zero rate to a discount factor.
    """
    return 1.0 / (1.0 + z * t)

def interpolate_df(tenors, z, T):
    """
    Linearly interpolates the zero rate for a specific time T, 
    then converts it to a discount factor.
    """
    z_interp = np.interp(T, tenors, z)
    return zero_to_df(z_interp, T)

def compute_swap_annuity_and_forward(z, tenors, T_exp, T_mat, pay_yy=2):
    """
    Calculates the annuity and forward swap rate (F) for a swaption.
    """
    dt = 1.0 / pay_yy
    n_pay = int(round(T_mat * pay_yy))
    
    if n_pay <= 0:
        return 0.0, 0.0

    times_cf = np.array([T_exp + dt * (i + 1) for i in range(n_pay)])
    dfs_cf = np.array([interpolate_df(tenors, z, t) for t in times_cf])
    
    annuity = np.sum(dt * dfs_cf)
    
    df_start = interpolate_df(tenors, z, T_exp)
    df_end = interpolate_df(tenors, z, T_exp + T_mat)
    
    if annuity > 0:
        fwd = (df_start - df_end) / annuity
    else:
        fwd = 0.0
        
    return annuity, fwd

# ============================================================
# 2) Black76
# ============================================================
def black_swaption_price(annuity, F, K, vol, T_expiry, payer=False):
    if vol <= 0 or T_expiry <= 0 or annuity <= 0:
        return 0.0
    eps = 1e-8
    if F < eps or K < eps:
        return 0.0
    sqrtT = np.sqrt(T_expiry)
    d1 = (np.log(F/K) + 0.5*vol*vol*T_expiry) / (vol*sqrtT)
    d2 = d1 - vol*sqrtT
    if payer:
        return annuity * (F*norm.cdf(d1) - K*norm.cdf(d2))
    else:
        return annuity * (K*norm.cdf(-d2) - F*norm.cdf(-d1))
    
# ============================================================
# 3) Portfolio Pricing Loop (Black-76)
# ============================================================

def evaluate_portfolio_black76(df_portfolio, eval_date, z_curve, tenors, vol=0.30):
    """
    Iterates through a portfolio dataframe and prices each strip using Black-76.
    
    Inputs:
    - df_portfolio: DataFrame outputted by the portfolio builder
    - eval_date: datetime.date object of the valuation date
    - z_curve, tenors: The interest rate curve arrays
    - vol_surface: constant for the sake of this notebook (set at 0.3)
    """
    if df_portfolio.empty:
        return 0

    total_portfolio_cost = 0

    for _, row in df_portfolio.iterrows():
        # 1. Extract parameters
        expiry_date = pd.to_datetime(row['OPTION_EXPIRY'])
        evaluation_date = pd.to_datetime(eval_date)
        T_exp = (expiry_date - evaluation_date).days / 365.25
        T_mat = float(row['SWAP_TENOR'])
        K = float(row['STRIKE'])
        notional = float(row['NOTIONAL'])

        # Skip expired options or zero-tenor swaps
        if T_exp <= 0 or T_mat <= 0:
            continue

        # 2. Calculate Annuity and Forward Rate
        annuity, fwd = compute_swap_annuity_and_forward(z_curve, tenors, T_exp, T_mat)

        # 3. Price the Swaption
        unit_price = black_swaption_price(annuity, fwd, K, vol, T_exp, payer=False)

        # 4. Scale by Notional
        scaled_price = unit_price * notional
        total_portfolio_cost += scaled_price

    return total_portfolio_cost