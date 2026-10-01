"""HW3 Part 5C: second source for revenue and net income via yfinance.
pip install yfinance   then   python hw03/yfinance_check.py AAPL"""
import sys
import yfinance as yf

ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
inc = yf.Ticker(ticker).quarterly_income_stmt          # columns = quarter end dates, newest first
for col in inc.columns[:4]:
    rev = inc.loc["Total Revenue", col] / 1e6
    ni = inc.loc["Net Income", col] / 1e6
    print(f"{ticker} quarter ended {col.date()}: Revenue ${rev:,.1f}M | Net Income ${ni:,.1f}M")
