"""Excel model: DCF sheet uses LIVE formulas (edit blue inputs and it recalculates);
Comps/Scenarios/Financials sheets are Python-computed snapshots."""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter as L
import valuation as V

BLUE, BLK = Font(name="Arial", color="0000FF"), Font(name="Arial")
BOLD, YEL = Font(name="Arial", bold=True), PatternFill("solid", fgColor="FFFF00")

def _df(ws, df, r0=1, fmt="#,##0.0;(#,##0.0);-"):
    for j, col in enumerate(df.columns, 1): ws.cell(r0, j, str(col)).font = BOLD
    for i, row in enumerate(df.itertuples(index=False), r0 + 1):
        for j, v in enumerate(row, 1):
            x = ws.cell(i, j, v if isinstance(v, str) else float(v)); x.font = BLK
            if not isinstance(v, str): x.number_format = fmt
    for j in range(1, len(df.columns) + 1): ws.column_dimensions[L(j)].width = 20

def build(path, c, p, peers):
    wb = Workbook(); ws = wb.active; ws.title = "DCF"; h = c["hist"]
    ws["A1"] = f"{c['name']} - DCF ({c['currency']}, illustrative inputs; blue = editable)"; ws["A1"].font = BOLD
    inp = [("Base revenue (FY last)", h["Revenue"].iloc[-1], "#,##0"), ("Base EBIT margin", h["EBIT"].iloc[-1] / h["Revenue"].iloc[-1], "0.0%"),
           ("Growth - year 1", p["g_start"], "0.0%"), ("Growth - year 5", p["g_end"], "0.0%"),
           ("Target EBIT margin (yr 5)", p["margin_end"], "0.0%"), ("Tax rate", p["tax"], "0.0%"),
           ("D&A % revenue", p["da"], "0.0%"), ("Capex % revenue", p["capex"], "0.0%"),
           ("NWC % of incremental revenue", p["nwc"], "0.0%"), ("WACC", p["wacc"], "0.0%"),
           ("Terminal growth", p["tg"], "0.0%"), ("Net debt", c["net_debt"], "#,##0"),
           ("Shares (cr)", c["shares"], "#,##0.0"), ("Current price", c["price"], "#,##0.00")]
    for i, (k, v, f) in enumerate(inp, 3):
        ws.cell(i, 1, k).font = BLK; x = ws.cell(i, 2, v); x.font = BLUE; x.number_format = f
        if k in ("WACC", "Terminal growth"): x.fill = YEL
    rows = ["Year index", "Revenue growth", "Revenue", "EBIT margin", "EBIT", "NOPAT", "D&A", "Capex",
            "Change in NWC", "Free cash flow", "Discount factor", "PV of FCF"]
    for k, name in enumerate(rows): ws.cell(18 + k, 1, name).font = BOLD if name in ("Revenue", "Free cash flow") else BLK
    for n in range(1, 6):
        col = L(n + 2); prev = L(n + 1)
        f = {18: n, 19: f"=$B$5+($B$6-$B$5)*({col}18-1)/4",
             20: f"=$B$3*(1+{col}19)" if n == 1 else f"={prev}20*(1+{col}19)",
             21: f"=$B$4+($B$7-$B$4)*{col}18/5", 22: f"={col}20*{col}21", 23: f"={col}22*(1-$B$8)",
             24: f"={col}20*$B$9", 25: f"={col}20*$B$10",
             26: f"=$B$11*({col}20-{'$B$3' if n == 1 else prev + '20'})",
             27: f"={col}23+{col}24-{col}25-{col}26", 28: f"=1/(1+$B$12)^{col}18", 29: f"={col}27*{col}28"}
        for r, v in f.items():
            x = ws[f"{col}{r}"]; x.value = v; x.font = BLK
            x.number_format = "0.0%" if r in (19, 21) else "0.000" if r == 28 else "0" if r == 18 else "#,##0.0;(#,##0.0);-"
    out = [("Sum of PV of FCF", "=SUM(C29:G29)"), ("Terminal value", "=G27*(1+B13)/(B12-B13)"),
           ("PV of terminal value", "=B32*G28"), ("Enterprise value", "=B31+B33"), ("Equity value", "=B34-B14"),
           ("Intrinsic value per share", "=B35/B15"), ("Upside vs current price", "=B36/B16-1")]
    for i, (k, f) in enumerate(out, 31):
        ws.cell(i, 1, k).font = BOLD if i >= 34 else BLK; x = ws.cell(i, 2, f); x.font = BLK
        x.number_format = "0.0%" if i == 37 else "#,##0.0"
    ws.column_dimensions["A"].width = 34
    for j in range(2, 8): ws.column_dimensions[L(j)].width = 13
    ws["A39"] = "Assumptions are illustrative placeholders, not sourced forecasts."
    # snapshot sheets
    s, cp = V.scenarios(c, p), V.comps(c, peers)
    w = wb.create_sheet("Comps"); _df(w, cp["table"])
    w.cell(len(peers) + 3, 1, "Implied price @ median P/E").font = BOLD; w.cell(len(peers) + 3, 2, cp["pe_px"][1])
    w.cell(len(peers) + 4, 1, "Implied price @ median EV/EBITDA").font = BOLD; w.cell(len(peers) + 4, 2, cp["ev_px"][1])
    w = wb.create_sheet("Scenarios")
    _df(w, pd.DataFrame([{"Scenario": k, "Value/share": v["price"], "EV": v["ev"], "TV % of EV": v["tv_share"]} for k, v in s.items()]))
    _df(wb.create_sheet("Football field"), V.football(c, p, peers))
    _df(wb.create_sheet("Historicals"), h)
    wb.save(path)
