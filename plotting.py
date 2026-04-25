# ============================================================
# 0) Imports
# ============================================================
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from PTF_construction import simulate_amortization_cpr

# ============================================================
# 1) Amortisation
# ============================================================
def plot_bands(payment_freq, maturity_years, N_0, mortgage_rate, base_CPR, exp_CPR, stress_CPR, start_date, apply_cpr=True):
    
    # 1. Simulate paths
    n_list_base, time_list, _ = simulate_amortization_cpr(payment_freq, maturity_years, N_0, mortgage_rate, base_CPR, start_date, apply_cpr=True)
    n_list_exp, _, _ = simulate_amortization_cpr(payment_freq, maturity_years, N_0, mortgage_rate, exp_CPR, start_date, apply_cpr=True)
    n_list_stress, _, _ = simulate_amortization_cpr(payment_freq, maturity_years, N_0, mortgage_rate, stress_CPR, start_date, apply_cpr=True)

    plt.figure(figsize=(10, 6))

    # 2. Plotting
    plt.plot(time_list, n_list_base, label=f"Baseline CPR ({base_CPR*100:.0f}%)")
    plt.plot(time_list, n_list_exp, label=f"Expected CPR ({exp_CPR*100:.0f}%)")
    plt.plot(time_list, n_list_stress, label=f"Max/Stress CPR ({stress_CPR*100:.0f}%)")

    # 3. Formatting
    plt.title("Amortisation Profile with Prepayment")
    plt.xlabel("Time (Years)")
    plt.ylabel("Outstanding Balance")
    plt.xlim(left=0, right=maturity_years)
    plt.ylim(bottom=0)
    
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()
    



