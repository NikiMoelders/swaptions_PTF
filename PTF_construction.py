# ============================================================
# 0) Imports
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt 
import itertools
import os 

# ============================================================
# 1) Mortgage Amortisation + Prepayment
# ============================================================


def simulate_amortization_cpr(payment_freq, maturity_years, N_0, K_rate, cpr, start_date, apply_cpr=True):
    """
    Inputs: Mortgage Payment Frequency (12 = monthly), Maturity Years (e.g. 2), Initial Principal, Mortgage Rate (e.g. 0.05),
             CPR (e.g. 0.05), Start Date (e.g. 01-01-2026), Apply CPR (Set at TRUE)

    Outputs: List of Residual Debt,
             List of Time in Years (hardcoded as steps in 6 months for visualisation),
             List of Actual Dates (e.g. 01-01-2026, 01-07-20206,...)
    """
    total_periods = int(maturity_years * payment_freq)
    
    # Standard Annuity Formula for Initial Payment (PMT)
    discount_factor = (1.0 + K_rate) ** (-total_periods)
    pmt = (K_rate * N_0) / (1.0 - discount_factor)

    n_list = []
    time_list = []
    date_list = []

    # Initial State 
    N_prev = N_0
    n_list.append(N_prev)
    time_list.append(0.0)
    date_list.append(start_date)
    current_date = start_date

    for i in range(1, total_periods + 1):
        
        # 1. Standard Amortization Components
        interest_payment = K_rate * N_prev
        principal_payment = pmt - interest_payment

        # 2. Outstanding Balance & Prepayment
        if apply_cpr and i < total_periods:
            standard_balance = N_prev - principal_payment
            prepayment_amount = cpr * standard_balance
            N_curr = standard_balance - prepayment_amount
        else:
            N_curr = N_prev - principal_payment

        # 3. Recalculate Annuity
        if apply_cpr and i < total_periods:
            remaining_periods = total_periods - i
            discount_factor = (1.0 + K_rate) ** (-remaining_periods)
            pmt = (K_rate * N_curr) / (1.0 - discount_factor)

        # 4. Step Time Forward (Hardcoded to 6 months for semi-annual grid)
        delta_time = relativedelta(months=6)
        current_date = current_date + delta_time

        # Store Results
        n_list.append(max(0, N_curr)) # Prevent negative balances
        time_list.append(i * 0.5)
        date_list.append(current_date)

        # Update for next iteration
        N_prev = N_curr

    return n_list, time_list, date_list

# ============================================================
# 2) Band Creation
# ============================================================

def build_amortization_bands(maturity_years, CPR, N0, K, ref_date, pay_yy=2, base_pp = 0.01):
    """

    Inputs: Maturity Years (e.g. 2), CPR (e.g. 0.05), Initial Principal,
            Mortgage Rate (e.g. 0.05), Start Date (e.g. 01-01-2026), Mortgage Payment Frequency (Set at 6 months),
            Baseline CPR (Set at 0.01)

    Outputs: List of Actual Dates (e.g. 01-01-2026, 01-07-20206,...)
             List of Residual Debt under baseline CPR
             List of Residual Debt under inputted CPR
             List of Time in Years (hardcoded as steps in 6 months for visualisation),
             
    Returns the Baseline expected path and the Stressed tail path.
    """

    upper_n, time_list, dates_upper = simulate_amortization_cpr(
        pay_yy, maturity_years, N0, K, base_pp, ref_date, True
    )
    lower_n, _, dates_lower = simulate_amortization_cpr(
        pay_yy, maturity_years, N0, K, CPR, ref_date, True
    )

    return dates_upper, upper_n, lower_n, time_list

# ============================================================
# 3) Portfolio Builder - Constant Prepayment Hedge
# ============================================================

def build_constant_prepay_ptf(dates, expected_n, lower_n, K, p_min=0.01):
    portfolio = []

    for i in range(1, len(dates)):
        # Calculate the gaps for the current and previous periods
        delta_curr = expected_n[i] - lower_n[i]
        delta_prev = expected_n[i-1] - lower_n[i-1]
        
        # Calculate the incremental notional (omega_i)
        notional = delta_curr - delta_prev * (1 - p_min)

        # Only add to portfolio if bigger than 0.01 = 0.01 % of N_0 
        if notional > 0.01: 
            tenor_years = (dates[-1] - dates[i]).days / 365.25
            row = {
                'OPTION_EXPIRY': dates[i],
                'SWAP_TENOR': tenor_years,
                'STRIKE': K,
                'NOTIONAL': notional,
                'TYPE': 'RECEIVER_ATM'
            }
            portfolio.append(row) 
            
    return pd.DataFrame(portfolio)

# ============================================================
# 4) Hybrid Portfolio Builder
# ============================================================

def build_hybrid_ptf(dates, N_min, N_exp, N_max, K, p_min=0.01):
    portfolio = []
    
    # from basel 3 (200 bps shock)
    K_OTM = K - 0.02 

    for i in range(1, len(dates)):
        
        delta_N_baseline_curr = N_min[i] - N_exp[i]
        delta_N_baseline_prev = N_min[i-1] - N_exp[i-1]
        
        delta_N_tail_curr = N_exp[i] - N_max[i]
        delta_N_tail_prev = N_exp[i-1] - N_max[i-1]

        # incremental strips (omega)
        omega_ATM = delta_N_baseline_curr - delta_N_baseline_prev * (1 - p_min)
        omega_OTM = delta_N_tail_curr - delta_N_tail_prev * (1 - p_min)

        tenor_years = (dates[-1] - dates[i]).days / 365.25

        #Again only consider actual notionals 

        # atm layer
        if omega_ATM > 0.01:
            portfolio.append({
                'OPTION_EXPIRY': dates[i],
                'SWAP_TENOR': tenor_years,
                'STRIKE': K,
                'NOTIONAL': omega_ATM,
                'TYPE': 'RECEIVER_ATM'
            })
            
        # otm layer
        if omega_OTM > 0.01:
            portfolio.append({
                'OPTION_EXPIRY': dates[i],
                'SWAP_TENOR': tenor_years,
                'STRIKE': K_OTM,
                'NOTIONAL': omega_OTM,
                'TYPE': 'RECEIVER_OTM'
            })
            
    return pd.DataFrame(portfolio)