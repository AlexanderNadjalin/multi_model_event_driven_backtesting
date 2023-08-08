# Things to mention
### Asset selection - comment
X-trackers?
### Single currency -> commission

# Items to handle
### Re-balancing on same date as signal

### Mark-to-market on close

### ~~Trades on average~~

### Commission incl. cost for shorts

# Structure
start_date, end_date - same for MP and all P

* ~~1 MP~~
* ~~add P1, ...~~
* run bt on P1, ...
* sum to MP

Eval on all P, and MP

# Flow
1. Set dates
2. Define market
3. Define master portfolio
   4. Define portfolios
   5. Add portfolios to master portfolio
6. Define portfolio strategies
   7. Add strategies to master portfolio
8. Define backtest
9. Run backtest
   10. Outer loop for dates
   11. New BAR event
   12. For each strategy in each portfolio:
       13. Inner loop for event handling
       14. BAR event - if there is a strategy, generate CALCSIGNAL event
       15. strategy.calc_signal - check and generate transaction
       16. TRANSACTION - handle