This repository contains an outline of the swaption portfolio construction and pricing models developed for my undergraduate BSc Mathematics thesis, "Hedging Mortgage Prepayment Risk" at University College Dublin. 

It constructs the residual debt paths of an annuity mortgage portfolio under different Conditional Prepayment Rates (CPR) and hedges their corresponding notionals using both ATM and OTM European Swaptions. The portfolios are priced under the Black-76 model. A toy example of parameters is provided in the Jupyter Notebook to more recent 2026 market data. My original thesis was based on private data from 31/12/2021 during the Eurozone's negative rate environment. As a result, the Hull-White model was utilised in the formal write-up.

## Codebase

The codebase is engineered to ensure mathematical rigour without the requirement of proprietary or external databases.

* **`plotting.py`**: Plots the amortisation profiles of different CPRs to visualize the interest rate exposure due to prepayment.
* **`PTF_construction.py`**: Constructs hedging portfolios as Pandas DataFrames:
  1. A constant prepayment hedging portfolio of European ATM swaptions with notionals corresponding to the gap between minimally prepaid and expected prepaid amortisation profiles.
  2. A hybrid portfolio containing both ATM swaptions and OTM swaptions with notionals corresponding to a stressed prepayment rate (accounting for interest rate shocks, hence the OTM strike).
* **`pricing.py`**: Prices each hedging portfolio under the Black-76 framework using a vectorized approach for computational speed.
* **`hedge.ipynb`**: The primary execution environment. It defines a toy example of macroeconomic variables (yield curves, volatility, mortgage rates vs. par strike rates), runs the builders, and outputs the final portfolio pricing.

## Dependencies

NumPy, SciPy, Pandas, Matplotlib

## Setup

```bash
git clone [https://github.com/NikiMoelders/swaptions_PTF.git](https://github.com/NikiMoelders/swaptions_PTF.git)
cd swaptions_PTF
pip install pandas numpy scipy matplotlib
```

## Contact

Please send any comments or suggestions to niklas.moelders@ucdconnect.ie. I am very open to discussing this project and the underlying mathematics!