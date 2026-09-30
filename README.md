# Equity Research & Stock Valuation Dashboard
Python | Pandas | Excel (openpyxl) | Streamlit + Plotly

## Run
    pip install -r requirements.txt
    python valuation.py          # console summary + Equity_Valuation_Model.xlsx
    streamlit run app.py         # interactive dashboard

## Files
- data.py         demo data (illustrative) + optional yfinance loader
- valuation.py    DCF, WACC/g sensitivity, P/E & EV/EBITDA comps, Bear/Base/Bull, football field
- export_excel.py Excel model; DCF sheet is live formulas (blue = inputs)
- app.py          dashboard

## Method
FCF = EBIT(1-t) + D&A - Capex - dNWC; growth fades linearly, margin converges to target.
EV = sum PV(FCF) + PV(Gordon terminal value); Equity = EV - net debt; per share = Equity / shares.
Peer value = median multiple x company metric (P/E on net income; EV/EBITDA less net debt).
Target = weighted DCF (Base) and average of comps; rating: >+15% BUY, <-10% SELL, else HOLD.

## Using a real company
Edit sample_company()/sample_peers() with figures from annual reports, or use from_yfinance().
Data here is fictional: results are not a real valuation or investment advice.
