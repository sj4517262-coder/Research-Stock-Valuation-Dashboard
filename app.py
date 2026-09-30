"""Run: streamlit run app.py"""
import io, pandas as pd, plotly.graph_objects as go, plotly.express as px, streamlit as st
import valuation as V
from data import sample_company, sample_peers
from export_excel import build

st.set_page_config(page_title="Equity Research Dashboard", layout="wide")
from data import from_yfinance
c, peers = from_yfinance("ITC.NS", ["HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS"])
h = c["hist"].copy(); h["EBITDA margin"] = h.EBITDA / h.Revenue; h["Growth"] = h.Revenue.pct_change()

st.title(f"{c['name']} ({c['ticker']}) - Equity Research & Valuation")
st.caption("Demo uses illustrative data. Replace via data.py to analyse a real company. Not investment advice.")

sb = st.sidebar; sb.header("DCF assumptions (Base case)")
p = dict(V.BASE)
p["g_start"] = sb.slider("Revenue growth yr 1", 0.0, .30, p["g_start"], .005, format="%.3f")
p["g_end"] = sb.slider("Revenue growth yr 5", 0.0, .20, p["g_end"], .005, format="%.3f")
p["margin_end"] = sb.slider("Target EBIT margin", .08, .30, p["margin_end"], .005, format="%.3f")
p["wacc"] = sb.slider("WACC", .07, .16, p["wacc"], .0025, format="%.4f")
p["tg"] = sb.slider("Terminal growth", .01, .06, p["tg"], .0025, format="%.4f")
p["tax"] = sb.slider("Tax rate", .15, .35, p["tax"], .01)
w_dcf = sb.slider("Weight on DCF in target", 0.0, 1.0, .5, .1)
if p["wacc"] <= p["tg"]: st.error("WACC must exceed terminal growth."); st.stop()

res, cp, sc = V.dcf(c, p), V.comps(c, peers), V.scenarios(c, p)
target = V.blended_target(sc, cp, w_dcf); rec, up = V.recommendation(c, target)

k = st.columns(5)
k[0].metric("Current price", f"{c['price']:.1f}"); k[1].metric("DCF value/share", f"{res['price']:.1f}", f"{res['price']/c['price']-1:+.0%}")
k[2].metric("Blended target", f"{target:.1f}", f"{up:+.0%}"); k[3].metric("Rating", rec)
k[4].metric("TV share of EV", f"{res['tv_share']:.0%}")

t1, t2, t3, t4, t5 = st.tabs(["Financials", "DCF", "Peer multiples", "Scenarios & football field", "Export"])
with t1:
    a, b = st.columns(2)
    a.plotly_chart(px.bar(h, x="Year", y=["Revenue", "EBITDA"], barmode="group", title="Revenue & EBITDA"), use_container_width=True)
    m = px.line(h.dropna(), x="Year", y=["Growth", "EBITDA margin"], markers=True, title="Growth & margin"); m.update_yaxes(tickformat=".0%")
    b.plotly_chart(m, use_container_width=True)
    st.dataframe(h.set_index("Year").style.format("{:,.2f}"), use_container_width=True)
with t2:
    d = res["table"]
    st.plotly_chart(px.bar(d, x="Year", y=["FCF", "PV of FCF"], barmode="group", title="Projected free cash flow"), use_container_width=True)
    st.dataframe(d.set_index("Year").style.format("{:,.2f}"), use_container_width=True)
    st.write(f"**EV** {res['ev']:,.0f} | **Equity** {res['equity']:,.0f} | **PV of TV** {res['pv_tv']:,.0f}")
    sens = V.sensitivity(c, p, [p["wacc"] + x for x in (-.02, -.01, 0, .01, .02)], [p["tg"] + x for x in (-.01, -.005, 0, .005, .01)])
    st.subheader("Value/share sensitivity (rows WACC, columns terminal growth)")
    st.dataframe(sens.style.format("{:.1f}").background_gradient(cmap="RdYlGn", axis=None), use_container_width=True)
with t3:
    tb = cp["table"]; st.dataframe(tb.set_index("Peer").style.format("{:,.1f}"), use_container_width=True)
    x = st.columns(2)
    x[0].plotly_chart(px.bar(tb, x="Peer", y="P/E", title=f"P/E (company: {cp['own_pe']:.1f}x)").add_hline(y=cp["own_pe"], line_dash="dot"), use_container_width=True)
    x[1].plotly_chart(px.bar(tb, x="Peer", y="EV/EBITDA", title=f"EV/EBITDA (company: {cp['own_ev']:.1f}x)").add_hline(y=cp["own_ev"], line_dash="dot"), use_container_width=True)
    st.write(f"Median-implied price: **P/E {cp['pe_px'][1]:.1f}**, **EV/EBITDA {cp['ev_px'][1]:.1f}**")
with t4:
    st.dataframe(pd.DataFrame({k: {"Value/share": v["price"], "EV": v["ev"], "TV % EV": v["tv_share"]} for k, v in sc.items()}).T.style.format("{:,.2f}"))
    ff = V.football(c, p, peers); fig = go.Figure(go.Bar(y=ff.Method, x=ff.High - ff.Low, base=ff.Low, orientation="h"))
    fig.add_vline(x=c["price"], line_dash="dash", annotation_text="Current"); fig.update_layout(title="Football field (value per share)")
    st.plotly_chart(fig, use_container_width=True)
with t5:
    buf = io.BytesIO(); build(buf, c, p, peers)
    st.download_button("Download Excel model (live-formula DCF)", buf.getvalue(), "Equity_Valuation_Model.xlsx")
