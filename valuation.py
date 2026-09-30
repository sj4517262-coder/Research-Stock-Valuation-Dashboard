"""Valuation engine: DCF, sensitivity, peer multiples, scenarios."""
import numpy as np, pandas as pd
from data import sample_company, sample_peers

BASE = dict(years=5, g_start=.12, g_end=.07, margin_end=.17, tax=.25, da=.038, capex=.055,
            nwc=.15, wacc=.115, tg=.04)
SCENARIOS = {"Bear": dict(g_start=.08, g_end=.05, margin_end=.145, wacc=.125, tg=.03),
             "Base": {},
             "Bull": dict(g_start=.15, g_end=.09, margin_end=.19, wacc=.105, tg=.05)}

def project(c, p):
    h = c["hist"]; rev0 = h["Revenue"].iloc[-1]; m0 = h["EBIT"].iloc[-1] / rev0; n = p["years"]
    g = np.linspace(p["g_start"], p["g_end"], n); m = np.linspace(m0, p["margin_end"], n + 1)[1:]
    df = pd.DataFrame({"Year": h["Year"].iloc[-1] + np.arange(1, n + 1), "Growth": g,
                       "Revenue": rev0 * np.cumprod(1 + g), "EBIT margin": m})
    df["EBIT"] = df.Revenue * df["EBIT margin"]; df["NOPAT"] = df.EBIT * (1 - p["tax"])
    df["D&A"] = df.Revenue * p["da"]; df["Capex"] = df.Revenue * p["capex"]
    df["Change in NWC"] = p["nwc"] * df.Revenue.diff().fillna(df.Revenue.iloc[0] - rev0)
    df["FCF"] = df.NOPAT + df["D&A"] - df.Capex - df["Change in NWC"]
    return df

def dcf(c, p):
    if p["wacc"] <= p["tg"]: raise ValueError("WACC must exceed terminal growth")
    df = project(c, p); t = np.arange(1, len(df) + 1)
    df["Discount factor"] = 1 / (1 + p["wacc"]) ** t; df["PV of FCF"] = df.FCF * df["Discount factor"]
    tv = df.FCF.iloc[-1] * (1 + p["tg"]) / (p["wacc"] - p["tg"]); pv_tv = tv * df["Discount factor"].iloc[-1]
    ev = df["PV of FCF"].sum() + pv_tv; eq = ev - c["net_debt"]
    return dict(table=df, tv=tv, pv_tv=pv_tv, ev=ev, equity=eq, price=eq / c["shares"], tv_share=pv_tv / ev)

def sensitivity(c, p, waccs, tgs):
    f = lambda w, g: dcf(c, {**p, "wacc": w, "tg": g})["price"] if w > g else np.nan
    return pd.DataFrame([[f(w, g) for g in tgs] for w in waccs],
                        index=[f"{w:.1%}" for w in waccs], columns=[f"{g:.1%}" for g in tgs])

def comps(c, peers):
    d = peers.copy(); d["P/E"] = d.MarketCap / d.NetIncome
    d["EV/EBITDA"] = (d.MarketCap + d.NetDebt) / d.EBITDA
    e = c["hist"]["EBITDA"].iloc[-1]
    pe_px = lambda x: x * c["net_income"] / c["shares"]
    ev_px = lambda x: (x * e - c["net_debt"]) / c["shares"]
    q = lambda col: d[col].quantile([.25, .5, .75]).values
    return dict(table=d, pe=q("P/E"), ev=q("EV/EBITDA"), pe_px=[pe_px(x) for x in q("P/E")],
                ev_px=[ev_px(x) for x in q("EV/EBITDA")],
                own_pe=c["price"] * c["shares"] / c["net_income"],
                own_ev=(c["price"] * c["shares"] + c["net_debt"]) / e)

def scenarios(c, p):
    return {k: dcf(c, {**p, **v}) for k, v in SCENARIOS.items()}

def football(c, p, peers):
    s, cp = scenarios(c, p), comps(c, peers)
    return pd.DataFrame([("DCF (Bear-Bull)", s["Bear"]["price"], s["Bull"]["price"]),
        ("P/E (25th-75th pct)", cp["pe_px"][0], cp["pe_px"][2]),
        ("EV/EBITDA (25th-75th pct)", cp["ev_px"][0], cp["ev_px"][2]),
        ("52-week range", c["low52"], c["high52"])], columns=["Method", "Low", "High"])

def recommendation(c, target):
    up = target / c["price"] - 1
    return ("BUY" if up > .15 else "SELL" if up < -.10 else "HOLD"), up

def blended_target(s, cp, w_dcf=.5):
    return w_dcf * s["Base"]["price"] + (1 - w_dcf) * (cp["pe_px"][1] + cp["ev_px"][1]) / 2

if __name__ == "__main__":
    from export_excel import build
    c, pe = sample_company(), sample_peers()
    s, cp = scenarios(c, BASE), comps(c, pe)
    for k, v in s.items(): print(f"{k:5s} DCF/share: {v['price']:.1f}")
    print("P/E implied (median):", round(cp["pe_px"][1], 1), "| EV/EBITDA implied:", round(cp["ev_px"][1], 1))
    t = blended_target(s, cp); print("Blended target:", round(t, 1), recommendation(c, t))
    build("Equity_Valuation_Model.xlsx", c, BASE, pe); print("Excel model written.")
