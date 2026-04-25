# ============================================================
# 0) Imports
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ============================================================
# 1) Amortisation
# ============================================================

def simulate_amortization_cpr(payment_freq, maturity_years, N_0, mortgage_rate, annual_cpr, start_date, apply_cpr=True):
    total_periods = int(maturity_years * payment_freq)
    periodic_cpr = 1.0 - (1.0 - annual_cpr) ** (1.0 / payment_freq)
    
    period_rate = mortgage_rate / payment_freq  

    discount_factor = (1.0 + period_rate) ** (-total_periods)  
    pmt = (period_rate * N_0) / (1.0 - discount_factor)       

    n_list = []
    time_list = []
    date_list = []

    N_prev = N_0
    n_list.append(N_prev)
    time_list.append(0.0)
    date_list.append(start_date)
    current_date = start_date

    for i in range(1, total_periods + 1):
        interest_payment = period_rate * N_prev 
        principal_payment = pmt - interest_payment

        if apply_cpr and i < total_periods:
            standard_balance = N_prev - principal_payment
            prepayment_amount = periodic_cpr * standard_balance
            N_curr = standard_balance - prepayment_amount
        else:
            N_curr = N_prev - principal_payment

        if apply_cpr and i < total_periods:
            remaining_periods = total_periods - i
            discount_factor = (1.0 + period_rate) ** (-remaining_periods)  
            pmt = (period_rate * N_curr) / (1.0 - discount_factor)        

        delta_time = relativedelta(months=int(12 / payment_freq))
        current_date = current_date + delta_time

        n_list.append(max(0, N_curr))
        time_list.append(i * (1.0 / payment_freq))
        date_list.append(current_date)

        N_prev = N_curr

    return n_list, time_list, date_list

# ============================================================
# 2) Band Creation
# ============================================================

def build_amortization_bands(maturity_years, CPR, N0, mortgage_rate, ref_date, pay_yy=2, base_pp=0.01):
    upper_n, time_list, dates_upper = simulate_amortization_cpr(
        pay_yy, maturity_years, N0, mortgage_rate, base_pp, ref_date, True
    )
    lower_n, _, dates_lower = simulate_amortization_cpr(
        pay_yy, maturity_years, N0, mortgage_rate, CPR, ref_date, True
    )

    return dates_upper, upper_n, lower_n, time_list

# ============================================================
# 3) Portfolio Builder - Constant Prepayment Hedge
# ============================================================

def build_constant_prepay_ptf(date, maturity_years, payment_freq, N_0, CPR_exp, mortgage_rate, strike_rate, CPR_min=0.01):
    """
    Inputs: 
    - Ref Date (e.g. 01-01-2026)
    - Maturity Years (e.g. 10)
    - Payment Frequency (12 = monthly, 2 = every 6 months)
    - Initial Principal
    - CPR (e.g. 0.08)
    - Mortgage Rate (Used for amortisation)
    - Strike Rate (Used for derivative pricing)
    - Baseline CPR (Set at 0.01)

    Output: Pandas Dataframe of Required Constant Prepayment Portfolio
    """

    lower_n, time_list, date_list = simulate_amortization_cpr(
        payment_freq, maturity_years, N_0, mortgage_rate, CPR_min, date, apply_cpr=True
    )
    expected_n, _, _ = simulate_amortization_cpr(
        payment_freq, maturity_years, N_0, mortgage_rate, CPR_exp, date, apply_cpr=True
    )

    p_min = 1.0 - (1.0 - CPR_min) ** (1.0 / payment_freq)  

    portfolio = []

    for i in range(1, len(date_list)):
        delta_curr = lower_n[i] - expected_n[i]      
        delta_prev = lower_n[i-1] - expected_n[i-1]  
        
        notional = delta_curr - (delta_prev * (1 - p_min)) 

        if notional > 0.01: 
            tenor_years = round((date_list[-1] - date_list[i]).days / 365.25, 2)
            row = {
                'OPTION_EXPIRY': date_list[i],
                'SWAP_TENOR': tenor_years,
                'STRIKE': strike_rate,
                'NOTIONAL': notional,
                'TYPE': 'RECEIVER_ATM'
            }
            portfolio.append(row) 
            
    return pd.DataFrame(portfolio)

# ============================================================
# 4) Hybrid Portfolio Builder
# ============================================================

def build_hybrid_ptf(date, maturity_years, payment_freq, N_0, CPR_exp, CPR_max, mortgage_rate, strike_rate, shock, CPR_min=0.01):
    """
    Inputs: 
    - Ref Date (e.g. 01-01-2026)
    - Maturity Years (e.g. 10)
    - Payment Frequency (12 = monthly, 2 = every 6 months)
    - Initial Principal
    - Expected CPR (e.g. 0.08)
    - Maximum CPR (e.g. 0.15)
    - Mortgage Rate (Used for amortisation)
    - Strike Rate (Used for derivative pricing)
    - Shock Rate for OTM Swaptions (Basel III recommends up to 0.02)
    - Baseline CPR (Set at 0.01)

    Output: Pandas Dataframe of Required Hybrid Portfolio
    """
    lower_n, time_list, date_list = simulate_amortization_cpr(
        payment_freq, maturity_years, N_0, mortgage_rate, CPR_min, date, apply_cpr=True
    )
    expected_n, _, _ = simulate_amortization_cpr(
        payment_freq, maturity_years, N_0, mortgage_rate, CPR_exp, date, apply_cpr=True
    )
    max_n, _, _ = simulate_amortization_cpr(
        payment_freq, maturity_years, N_0, mortgage_rate, CPR_max, date, apply_cpr=True
    )

    p_min = 1.0 - (1.0 - CPR_min) ** (1.0 / payment_freq) 

    portfolio = []
    
    K_OTM = strike_rate - shock 

    for i in range(1, len(date_list)):
        
        delta_baseline_curr = lower_n[i] - expected_n[i]    
        delta_baseline_prev = lower_n[i-1] - expected_n[i-1] 
        
        delta_tail_curr = expected_n[i] - max_n[i]
        delta_tail_prev = expected_n[i-1] - max_n[i-1]

        omega_ATM = delta_baseline_curr - (delta_baseline_prev * (1 - p_min)) 
        omega_OTM = delta_tail_curr - (delta_tail_prev * (1 - p_min))         

        tenor_years = round((date_list[-1] - date_list[i]).days / 365.25, 2)

        if omega_ATM > 0.01:
            portfolio.append({
                'OPTION_EXPIRY': date_list[i],
                'SWAP_TENOR': tenor_years,
                'STRIKE': strike_rate,
                'NOTIONAL': omega_ATM,
                'TYPE': 'RECEIVER_ATM'
            })
            
        if omega_OTM > 0.01:
            portfolio.append({
                'OPTION_EXPIRY': date_list[i],
                'SWAP_TENOR': tenor_years,
                'STRIKE': K_OTM,
                'NOTIONAL': omega_OTM,
                'TYPE': 'RECEIVER_OTM'
            })
            
    return pd.DataFrame(portfolio)