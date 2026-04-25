This repository contains the an outline of the swaption portfolio constructions and pricing models developed for my undergraduate BSc Mathematics thesis "Hedging Mortgage Prepayment Risk" at University College Dublin. It constructs the residual debt paths of an annuity mortgage portfolio under different Conditional Prepayment Rates (CPR) and hedges their corresponding notionals using both ATM and OTM European Swaptions. The portfolios are prices under the Black 76 model. A toy example of parameters are found in the Jupyter Notebook to reflect 2026 market data. My thesis was based on private data from 31/12/2021 during the Eurozone's negative rates and as a result the Hull-White model was used in my writeup.

Codebase

The codebase is engineered to ensure mathematical rigour without the requirement of propietary and external databases.

- plotting.py plots the amortisation profiles of different CPRs to understand the interest rate exposure due to prepayment.

- PTF_construction.py constructs hedging portfolios as a Pandas Dataframe:
  - 1) a constant prepayment hedging portfolio of European ATM swaptions with notionals corresponding to the gap between minimally prepaid and expected prepaid amortisation profiles
  - 2) A hybrid portfolio containing both ATM swaptions and OTM swaptions with notionals corresponding to a stressed prepayment rate, due to interest rate shocks, hence the OTM strike

- pricing.py prices each hedging portfolio under the Black 76 Framework using a vectorised approach for speed

- hedge.ipynb is execution environment. It defines the macroeconomic variables (yield curves, volatility, mortgage rates vs. par strike rates), runs the builders and outputs the        final portfolio pricing.

Dependencies:

