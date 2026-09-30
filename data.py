"""Data layer. Default = ILLUSTRATIVE demo data (fictional 'Demo Consumer Ltd', INR crore).
Swap in real numbers by editing sample_company()/sample_peers() or calling from_yfinance()."""
import pandas as pd

def sample_company():
    h = pd.DataFrame({"Year": [2021, 2022, 2023, 2024, 2025],
        "Revenue": [820, 940, 1075, 1230, 1395], "EBITDA": [148, 172, 204, 238, 272],
        "D&A": [32, 36, 41, 47, 53], "Capex": [45, 52, 60, 68, 76]})
    h["EBIT"] = h["EBITDA"] - h["D&A"]
    return dict(name="Demo Consumer Ltd", ticker="DEMO", hist=h, price=50.0, shares=50.0,
                net_debt=150.0, net_income=153.0, low52=41.0, high52=63.0, currency="INR Cr")

def sample_peers():
    return pd.DataFrame({"Peer": ["Alpha Foods", "Beta Brands", "Gamma Care", "Delta Retail", "Epsilon Bev", "Zeta Home"],
        "MarketCap": [9200, 6100, 12500, 4300, 7800, 3500], "NetDebt": [800, -200, 1500, 900, 400, 300],
        "EBITDA": [780, 470, 1150, 520, 610, 330], "NetIncome": [450, 300, 560, 170, 330, 140]})

def from_yfinance(ticker, peer_tickers=()):
    """Best-effort live loader (needs internet + `pip install yfinance`; field names vary by ticker)."""
    import yfinance as yf
    t = yf.Ticker(ticker); f, cf, info = t.financials, t.cashflow, t.info
    g = lambda df, k: df.loc[k].iloc[::-1] / 1e7 if k in df.index else None   # raw -> crore
    h = pd.DataFrame({"Year": [d.year for d in f.columns[::-1]], "Revenue": g(f, "Total Revenue").values,
        "EBITDA": g(f, "EBITDA").values, "D&A": g(f, "Reconciled Depreciation").values,
        "Capex": (-g(cf, "Capital Expenditure")).values[-len(f.columns):]})
    h["EBIT"] = h["EBITDA"] - h["D&A"]
    c = dict(name=info.get("shortName", ticker), ticker=ticker, hist=h.dropna(), price=info["currentPrice"],
             shares=info["sharesOutstanding"] / 1e7, net_debt=(info.get("totalDebt", 0) - info.get("totalCash", 0)) / 1e7,
             net_income=info["netIncomeToCommon"] / 1e7, low52=info["fiftyTwoWeekLow"], high52=info["fiftyTwoWeekHigh"], currency="INR Cr")
    rows = []
    for p in peer_tickers:
        i = yf.Ticker(p).info
        rows.append(dict(Peer=i.get("shortName", p), MarketCap=i["marketCap"] / 1e7,
            NetDebt=(i.get("totalDebt", 0) - i.get("totalCash", 0)) / 1e7, EBITDA=i["ebitda"] / 1e7,
            NetIncome=i["netIncomeToCommon"] / 1e7))
    return c, pd.DataFrame(rows)
