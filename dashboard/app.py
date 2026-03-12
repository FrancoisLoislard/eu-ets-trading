"""
dashboard/app.py  —  EU-ETS Trading Dashboard
4 tabs: Market Context | Price & Technicals | Seasonality | Energy Correlations
Run:  streamlit run dashboard/app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(page_title="EU-ETS Trading", page_icon="🌍",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;background:#0D1117;color:#E6EDF3}
.dash-title{font-family:'IBM Plex Mono',monospace;font-size:1.5rem;font-weight:600;color:#3FB950}
.dash-sub{font-size:.82rem;color:#8B949E;text-transform:uppercase;letter-spacing:.5px}
.live{display:inline-block;background:#1A3A1A;color:#3FB950;border:1px solid #3FB950;
  border-radius:20px;font-size:.68rem;padding:2px 10px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.kpi-grid{display:flex;gap:12px;margin:12px 0;flex-wrap:wrap}
.kpi-card{background:#161B22;border:1px solid #21262D;border-radius:8px;padding:14px 18px;flex:1;min-width:120px}
.kpi-card.up{border-top:3px solid #3FB950}.kpi-card.dn{border-top:3px solid #F85149}.kpi-card.nu{border-top:3px solid #58A6FF}
.kl{font-size:.72rem;color:#8B949E;text-transform:uppercase;letter-spacing:.8px;margin-bottom:5px}
.kv{font-family:'IBM Plex Mono',monospace;font-size:1.35rem;font-weight:600;color:#E6EDF3}
.kd{font-family:'IBM Plex Mono',monospace;font-size:.78rem;margin-top:3px}
.kd.up{color:#3FB950}.kd.dn{color:#F85149}.kd.nu{color:#58A6FF}
.sec{font-family:'IBM Plex Mono',monospace;font-size:.82rem;color:#3FB950;text-transform:uppercase;
  letter-spacing:1.5px;border-bottom:1px solid #21262D;padding-bottom:5px;margin:16px 0 10px}
.ibox{background:#161B22;border-left:3px solid #58A6FF;border-radius:0 6px 6px 0;
  padding:12px 16px;margin:8px 0;font-size:.88rem;color:#C9D1D9;line-height:1.6}
.wbox{background:#1C1A12;border-left:3px solid #D29922;border-radius:0 6px 6px 0;
  padding:12px 16px;margin:8px 0;font-size:.88rem;color:#C9D1D9;line-height:1.6}
.dt{width:100%;border-collapse:collapse;font-size:.85rem}
.dt th{background:#21262D;color:#8B949E;font-weight:600;text-align:left;padding:8px 12px;font-size:.75rem;text-transform:uppercase;letter-spacing:.8px}
.dt td{padding:8px 12px;border-bottom:1px solid #21262D;color:#C9D1D9}
.dt tr:last-child td{border-bottom:none}
.tup{background:#1A3A1A;color:#3FB950;padding:2px 8px;border-radius:4px;font-size:.75rem}
.tdn{background:#3A1A1A;color:#F85149;padding:2px 8px;border-radius:4px;font-size:.75rem}
.tvl{background:#1A2A3A;color:#58A6FF;padding:2px 8px;border-radius:4px;font-size:.75rem}
.rw{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #21262D}
.stTabs [data-baseweb="tab-list"]{background:#161B22;border-bottom:2px solid #21262D;gap:0}
.stTabs [data-baseweb="tab"]{font-size:.85rem;font-weight:600;color:#8B949E;padding:10px 22px}
.stTabs [aria-selected="true"]{color:#3FB950!important;border-bottom:2px solid #3FB950!important;background:transparent!important}
section[data-testid="stSidebar"]{background:#161B22;border-right:1px solid #21262D}
section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] p{color:#C9D1D9!important}
#MainMenu,footer,header{visibility:hidden}
</style>""", unsafe_allow_html=True)

G="#3FB950"; R="#F85149"; B="#58A6FF"; Y="#D29922"; P="#BC8CFF"; GR="#8B949E"
PAL=[G,Y,B,P]
PL=dict(plot_bgcolor="#0D1117",paper_bgcolor="#161B22",
        font=dict(family="IBM Plex Sans",color="#C9D1D9",size=12),
        xaxis=dict(gridcolor="#21262D",linecolor="#30363D"),
        yaxis=dict(gridcolor="#21262D",linecolor="#30363D"),
        legend=dict(bgcolor="#161B22",bordercolor="#21262D",borderwidth=1),
        margin=dict(l=50,r=30,t=40,b=40))

@st.cache_data(ttl=3600)
def load(ticker, period="2y"):
    try:
        df=yf.download(ticker,period=period,auto_adjust=True,progress=False)
        if df.empty: return pd.DataFrame()
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

def add_ind(df):
    if df.empty or "Close" not in df.columns: return df
    c=df["Close"]
    df["EMA20"]=c.ewm(span=20,adjust=False).mean()
    df["EMA50"]=c.ewm(span=50,adjust=False).mean()
    df["SMA200"]=c.rolling(200).mean()
    d=c.diff(); ga=d.clip(lower=0).rolling(14).mean(); lo=(-d.clip(upper=0)).rolling(14).mean()
    df["RSI"]=100-100/(1+ga/lo.replace(0,np.nan))
    sma=c.rolling(20).mean(); std=c.rolling(20).std()
    df["BBhi"]=sma+2*std; df["BBlo"]=sma-2*std
    df["R1"]=c.pct_change(); df["R5"]=c.pct_change(5)
    df["V20"]=df["R1"].rolling(20).std()*np.sqrt(252)
    return df

PMAP={"6 months":"6mo","1 year":"1y","2 years":"2y","5 years":"5y"}
with st.sidebar:
    st.markdown("### ⚙️ Settings"); st.markdown("---")
    period=PMAP[st.selectbox("Analysis period",list(PMAP.keys()),index=2)]
    st.markdown("---"); st.markdown("**Chart overlays**")
    s_ema=st.checkbox("EMA 20/50",value=True); s_bb=st.checkbox("Bollinger Bands",value=True)
    s_vol=st.checkbox("Volume",value=True); s_rsi=st.checkbox("RSI (14)",value=True)
    s_sma=st.checkbox("SMA 200",value=False)
    st.markdown("---")
    if st.button("🔄 Refresh",use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown(f"<p style='color:#8B949E;font-size:.75rem'>Updated: {datetime.now().strftime('%H:%M:%S')}</p>",unsafe_allow_html=True)

with st.spinner("Loading market data..."):
    df_e=add_ind(load("CO2.L",period=period))
    df_g=load("TTF=F",period=period)
    df_b=load("BZ=F",period=period)
    df_s=load("^STOXX50E",period=period)

if df_e.empty:
    st.error("❌ Could not load EUA data (CO2.L). Check your internet connection."); st.stop()

lx=float(df_e["Close"].iloc[-1]); px_=float(df_e["Close"].iloc[-2])
c1d=(lx-px_)/px_*100; c5d=float(df_e["R5"].iloc[-1])*100
v20=float(df_e["V20"].iloc[-1])*100; rv=float(df_e["RSI"].iloc[-1])
hi=float(df_e["Close"].rolling(min(252,len(df_e))).max().iloc[-1])
lo_=float(df_e["Close"].rolling(min(252,len(df_e))).min().iloc[-1])
rl="Overbought" if rv>70 else ("Oversold" if rv<30 else "Neutral")
rc_="dn" if rv>70 else ("up" if rv<30 else "nu")

st.markdown(f"""
<p class="dash-title">🌍 EU-ETS TRADING DASHBOARD <span class="live">● LIVE</span></p>
<p class="dash-sub">European Union Allowances (EUA) — Market Intelligence Platform</p>
<div class="kpi-grid">
  <div class="kpi-card {'up' if c1d>=0 else 'dn'}">
    <div class="kl">EUA Price (€/tCO₂)</div><div class="kv">€{lx:.2f}</div>
    <div class="kd {'up' if c1d>=0 else 'dn'}">{'▲' if c1d>=0 else '▼'} {c1d:+.2f}% today</div></div>
  <div class="kpi-card {'up' if c5d>=0 else 'dn'}">
    <div class="kl">5-Day Return</div><div class="kv">{c5d:+.2f}%</div>
    <div class="kd {'up' if c5d>=0 else 'dn'}">vs last week</div></div>
  <div class="kpi-card nu">
    <div class="kl">Volatility 20d ann.</div><div class="kv">{v20:.1f}%</div>
    <div class="kd nu">annualized</div></div>
  <div class="kpi-card {rc_}">
    <div class="kl">RSI 14-day</div><div class="kv">{rv:.1f}</div>
    <div class="kd {rc_}">{rl}</div></div>
  <div class="kpi-card nu">
    <div class="kl">52-Week Range</div><div class="kv">€{lo_:.0f}–{hi:.0f}</div>
    <div class="kd nu">low / high</div></div>
</div>""", unsafe_allow_html=True)

t1,t2,t3,t4=st.tabs(["🏭  Market Context","📈  Price & Technicals","📅  Seasonality","🔗  Energy Correlations"])

# ─── TAB 1 — MARKET CONTEXT ──────────────────────────────────────────────────
with t1:
    ca,cb=st.columns([3,2])
    with ca:
        st.markdown('<div class="sec">What is the EU-ETS?</div>',unsafe_allow_html=True)
        st.markdown("""<div class="ibox">The <b>EU Emissions Trading System</b> is the world's largest carbon market (since 2005),
covering ~40% of EU greenhouse gas emissions across power, industry and aviation.<br><br>
<b>Core rule:</b> each installation surrenders <b>1 EUA per tonne of CO₂</b> by <b>April 30</b> each year.
EUAs are bought at auction (ICE/EEX) or on secondary markets.</div>""",unsafe_allow_html=True)
        st.markdown('<div class="sec">EU-ETS Phases</div>',unsafe_allow_html=True)
        ph=[("Phase 1","2005–2007","Pilot — over-allocation, price collapsed to ~€0"),
            ("Phase 2","2008–2012","Kyoto period — financial crisis crushed demand"),
            ("Phase 3","2013–2020","Unified EU cap; MSR introduced 2019"),
            ("Phase 4","2021–2030","Fit-for-55: cap −4.2%/yr → prices hit €100+")]
        rows="".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a,b,c in ph)
        st.markdown(f'<table class="dt"><thead><tr><th>Phase</th><th>Years</th><th>Key Points</th></tr></thead><tbody>{rows}</tbody></table>',unsafe_allow_html=True)
        st.markdown('<div class="sec">Fuel Switching Economics</div>',unsafe_allow_html=True)
        st.markdown("""<div class="ibox">
<b>Clean Spark Spread</b> = Power − (Gas/eff) − (EUA × 0.20 tCO₂/MWh)<br>
<b>Clean Dark Spread</b> = Power − (Coal/eff) − (EUA × 0.34 tCO₂/MWh)<br><br>
When Dark > Spark → plants burn coal → more CO₂ → <b>EUA demand and price rise</b>.</div>""",unsafe_allow_html=True)
    with cb:
        st.markdown('<div class="sec">Market Facts (2024)</div>',unsafe_allow_html=True)
        mf=[("Market turnover","~€800bn/year"),("EUA price range","€50–€105/tCO₂"),
            ("Compliance deadline","April 30"),("Installations","~11,000 across EU"),
            ("Exchanges","ICE Endex, EEX"),("Yahoo ticker","CO2.L"),("Contract size","1,000 EUAs"),("Cap reduction","4.2%/yr Phase 4")]
        rows="".join(f"<tr><td><b>{k}</b></td><td style='color:#3FB950;font-family:IBM Plex Mono,monospace'>{v}</td></tr>" for k,v in mf)
        st.markdown(f'<table class="dt"><tbody>{rows}</tbody></table>',unsafe_allow_html=True)
        st.markdown('<div class="sec">MSR</div>',unsafe_allow_html=True)
        st.markdown("""<div class="wbox">The <b>Market Stability Reserve</b> (2019) automatically withdraws EUAs when
supply exceeds 833M. Since 2023, excess allowances are <b>permanently cancelled</b> — structural price support.</div>""",unsafe_allow_html=True)
    st.markdown('<div class="sec">Key Price Drivers</div>',unsafe_allow_html=True)
    cd1,cd2=st.columns(2)
    dl=[("Gas Price ↑","EUA ↑","tup","Coal cheaper → fuel switch → more CO₂/MWh"),
        ("Coal Price ↑","EUA ↓","tdn","Gas cheaper → less CO₂/MWh"),
        ("Cold weather","EUA ↑","tup","More energy demand → more emissions"),
        ("Industrial output ↑","EUA ↑","tup","More production → more compliance need")]
    dr=[("Regulation tightening","Volatile","tvl","Cap tightening → strong price spike"),
        ("MSR absorption","EUA ↑","tup","Supply permanently withdrawn"),
        ("CBAM","EUA ↑","tup","Reduces carbon leakage, price floor"),
        ("Renewables surge","EUA ↓","tdn","Less fossil fuel → lower demand")]
    with cd1:
        rows="".join(f'<tr><td><b>{d}</b></td><td><span class="{c}">{i}</span></td><td style="font-size:.8rem;color:#8B949E">{e}</td></tr>' for d,i,c,e in dl)
        st.markdown(f'<table class="dt"><thead><tr><th>Driver</th><th>Impact</th><th>Why</th></tr></thead><tbody>{rows}</tbody></table>',unsafe_allow_html=True)
    with cd2:
        rows="".join(f'<tr><td><b>{d}</b></td><td><span class="{c}">{i}</span></td><td style="font-size:.8rem;color:#8B949E">{e}</td></tr>' for d,i,c,e in dr)
        st.markdown(f'<table class="dt"><thead><tr><th>Driver</th><th>Impact</th><th>Why</th></tr></thead><tbody>{rows}</tbody></table>',unsafe_allow_html=True)

# ─── TAB 2 — PRICE & TECHNICALS ──────────────────────────────────────────────
with t2:
    st.markdown('<div class="sec">EUA Price Chart (CO2.L)</div>',unsafe_allow_html=True)
    nr=1+int(s_vol)+int(s_rsi)
    fig=make_subplots(rows=nr,cols=1,shared_xaxes=True,vertical_spacing=.04,row_heights=[.6]+[.2]*(nr-1))
    r=1
    if all(c in df_e.columns for c in ["Open","High","Low","Close"]):
        fig.add_trace(go.Candlestick(x=df_e.index,open=df_e["Open"],high=df_e["High"],
            low=df_e["Low"],close=df_e["Close"],name="EUA",
            increasing_line_color=G,increasing_fillcolor=G,
            decreasing_line_color=R,decreasing_fillcolor=R),row=r,col=1)
    if s_ema:
        fig.add_trace(go.Scatter(x=df_e.index,y=df_e["EMA20"],name="EMA 20",line=dict(color=Y,width=1.5)),row=r,col=1)
        fig.add_trace(go.Scatter(x=df_e.index,y=df_e["EMA50"],name="EMA 50",line=dict(color=B,width=1.5)),row=r,col=1)
    if s_sma:
        fig.add_trace(go.Scatter(x=df_e.index,y=df_e["SMA200"],name="SMA 200",line=dict(color=P,width=1.5,dash="dot")),row=r,col=1)
    if s_bb:
        fig.add_trace(go.Scatter(x=df_e.index,y=df_e["BBhi"],name="BB Upper",line=dict(color="rgba(88,166,255,.35)",width=1,dash="dot")),row=r,col=1)
        fig.add_trace(go.Scatter(x=df_e.index,y=df_e["BBlo"],name="BB Lower",
            line=dict(color="rgba(88,166,255,.35)",width=1,dash="dot"),fill="tonexty",fillcolor="rgba(88,166,255,.05)"),row=r,col=1)
    if s_vol and "Volume" in df_e.columns:
        r+=1
        bc=[G if x>=0 else R for x in df_e["R1"].fillna(0)]
        fig.add_trace(go.Bar(x=df_e.index,y=df_e["Volume"],marker_color=bc,showlegend=False),row=r,col=1)
        fig.update_yaxes(title_text="Volume",title_font=dict(size=10),row=r,col=1)
    if s_rsi and "RSI" in df_e.columns:
        r+=1
        fig.add_trace(go.Scatter(x=df_e.index,y=df_e["RSI"],name="RSI",line=dict(color=P,width=1.5)),row=r,col=1)
        fig.add_hline(y=70,line_dash="dash",line_color=R,opacity=.5,row=r,col=1)
        fig.add_hline(y=30,line_dash="dash",line_color=G,opacity=.5,row=r,col=1)
        fig.add_hrect(y0=70,y1=100,fillcolor=R,opacity=.04,row=r,col=1)
        fig.add_hrect(y0=0,y1=30,fillcolor=G,opacity=.04,row=r,col=1)
        fig.update_yaxes(title_text="RSI",range=[0,100],row=r,col=1)
        fig.update_layout(**PL,height=620,xaxis_rangeslider_visible=False)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.01,xanchor="right",x=1,
            bgcolor="rgba(22,27,34,.85)",font=dict(size=11)))
    st.plotly_chart(fig,use_container_width=True)
    ss1,ss2,ss3=st.columns(3)
    cl=df_e["Close"]
    def sr(l,v,col): return f'<div class="rw"><span style="color:#8B949E;font-size:.85rem">{l}</span><span style="font-family:IBM Plex Mono,monospace;color:{col};font-size:.85rem">{v}</span></div>'
    with ss1:
        st.markdown("**Returns**")
        for l,fn in [("1-day",lambda:cl.pct_change().iloc[-1]*100),("5-day",lambda:cl.pct_change(5).iloc[-1]*100),
                     ("1-month",lambda:cl.pct_change(21).iloc[-1]*100),("3-month",lambda:cl.pct_change(63).iloc[-1]*100)]:
            v=fn(); st.markdown(sr(l,f"{v:+.2f}%",G if v>=0 else R),unsafe_allow_html=True)
    with ss2:
        st.markdown("**Volatility & Risk**")
        for l,v in [("Vol 10d",f"{float(cl.pct_change().rolling(10).std().iloc[-1])*np.sqrt(252)*100:.1f}%"),
                    ("Vol 20d",f"{float(cl.pct_change().rolling(20).std().iloc[-1])*np.sqrt(252)*100:.1f}%"),
                    ("Vol 60d",f"{float(cl.pct_change().rolling(60).std().iloc[-1])*np.sqrt(252)*100:.1f}%"),
                    ("Max DD",f"{float((cl/cl.cummax()-1).min()*100):.1f}%"),("RSI",f"{rv:.1f}")]:
            st.markdown(sr(l,v,B),unsafe_allow_html=True)
    with ss3:
        st.markdown("**Price Levels**")
        for l,v in [("Current",f"€{lx:.2f}"),("EMA 20",f"€{float(df_e['EMA20'].iloc[-1]):.2f}"),
                    ("EMA 50",f"€{float(df_e['EMA50'].iloc[-1]):.2f}"),
                    ("BB Upper",f"€{float(df_e['BBhi'].iloc[-1]):.2f}"),("BB Lower",f"€{float(df_e['BBlo'].iloc[-1]):.2f}")]:
            st.markdown(sr(l,v,Y),unsafe_allow_html=True)
    with st.expander("🔍 Raw data — last 30 trading days"):
        cols=[c for c in ["Close","Volume","EMA20","EMA50","RSI","V20"] if c in df_e.columns]
        st.dataframe(df_e[cols].tail(30).round(3).sort_index(ascending=False),use_container_width=True)

# ─── TAB 3 — SEASONALITY ─────────────────────────────────────────────────────
with t3:
    MO=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    BS=[.3,.4,.6,.8,-.5,-.2,-.1,.0,.2,.3,.4,.5]
    nm=datetime.now().month
    cs1,cs2=st.columns([2,3])
    with cs1:
        st.markdown('<div class="sec">Monthly Seasonal Bias</div>',unsafe_allow_html=True)
        fs=go.Figure(go.Bar(x=MO,y=BS,
            marker_color=[G if b>.1 else(R if b<-.1 else GR) for b in BS],
            text=[f"{b:+.1f}" for b in BS],textposition="outside",
            textfont=dict(size=11,family="IBM Plex Mono")))
        fs.add_vline(x=nm-1,line_color=Y,line_width=2.5,
            annotation_text=f"← {MO[nm-1]}",annotation_font=dict(color=Y,size=11))
        fs.update_layout(**PL,height=320,showlegend=False,
            yaxis=dict(title="Bias score",range=[-.8,1.2],gridcolor="#21262D"))
        st.plotly_chart(fs,use_container_width=True)
    with cs2:
        st.markdown('<div class="sec">Month-by-Month Calendar</div>',unsafe_allow_html=True)
        cal=[("Jan","+","New compliance year. Auctions restart."),
             ("Feb","++","Compliance prep begins. Buying builds."),
             ("Mar","+++","EUTL publishes verified emissions → uncertainty spike."),
             ("Apr","++++","⚠️ COMPLIANCE DEADLINE April 30. Peak buying."),
             ("May","----","Post-compliance selloff. Surplus EUAs dumped."),
             ("Jun","--","Continued unwinding of positions."),
             ("Jul","-","Summer lull. Thin volumes."),
             ("Aug","=","Neutral. Holiday period."),
             ("Sep","+","Q3 reports. Early year-end positioning."),
             ("Oct","+","Heating season. Gas/power demand rises."),
             ("Nov","++","Year-end prep. Institutional buying."),
             ("Dec","+++","Year-end buying. Low auction supply.")]
        rows=""
        for m,sc,desc in cal:
            hl="background:#1C2A1C;" if m==MO[nm-1] else ""
            sc_=G if "+" in sc else(R if "-" in sc else GR)
            rows+=f'<tr style="{hl}"><td><b>{m}</b></td><td style="font-family:IBM Plex Mono,monospace;color:{sc_}">{sc}</td><td style="font-size:.8rem;color:#8B949E">{desc}</td></tr>'
        st.markdown(f'<table class="dt"><thead><tr><th>Month</th><th>Bias</th><th>Dynamics</th></tr></thead><tbody>{rows}</tbody></table>',unsafe_allow_html=True)
    st.markdown('<div class="sec">Historical Monthly Returns Heatmap</div>',unsafe_allow_html=True)
    mly=df_e["Close"].resample("ME").last().pct_change()*100
    mdf=mly.to_frame("R"); mdf["Year"]=mdf.index.year; mdf["Month"]=mdf.index.month
    if len(mdf)>12:
        pv=mdf.pivot_table(index="Year",columns="Month",values="R")
        pv.columns=[MO[m-1] for m in pv.columns]
        fh=px.imshow(pv,color_continuous_scale=[[0,R],[.5,"#21262D"],[1,G]],zmin=-15,zmax=15,text_auto=".1f",aspect="auto")
        fh.update_layout(**PL,height=300)
        fh.update_traces(textfont=dict(size=10,family="IBM Plex Mono"))
        st.plotly_chart(fh,use_container_width=True)
        st.caption("Monthly returns (%) — CO2.L adjusted close. Green = positive, red = negative.")
    else:
        st.info("Select 2y or 5y period to display heatmap.")

# ─── TAB 4 — ENERGY CORRELATIONS ─────────────────────────────────────────────
with t4:
    ast={"EUA (CO2.L)":df_e}
    if not df_g.empty and "Close" in df_g.columns: ast["Gas TTF"]=df_g
    if not df_b.empty and "Close" in df_b.columns: ast["Brent"]=df_b
    if not df_s.empty and "Close" in df_s.columns: ast["EuroStoxx 50"]=df_s
    st.markdown('<div class="sec">Normalized Price Performance (base 100)</div>',unsafe_allow_html=True)
    fn_=go.Figure()
    for i,(nm_,df_) in enumerate(ast.items()):
        s=df_["Close"].dropna()
        if len(s)>1: fn_.add_trace(go.Scatter(x=s.index,y=s/s.iloc[0]*100,name=nm_,line=dict(color=PAL[i%len(PAL)],width=2)))
    fn_.add_hline(y=100,line_dash="dot",line_color=GR,opacity=.4)
    fn_.update_layout(**PL,height=320,yaxis_title="Index (start = 100)")
    st.plotly_chart(fn_,use_container_width=True)
    rets={nm_:df_["Close"].pct_change() for nm_,df_ in ast.items() if "Close" in df_.columns}
    rdf=pd.DataFrame(rets).dropna()
    cc1,cc2=st.columns([1,2])
    with cc1:
        st.markdown('<div class="sec">Correlation Matrix</div>',unsafe_allow_html=True)
        if len(rdf.columns)>1:
            fcm=px.imshow(rdf.corr(),color_continuous_scale=[[0,R],[.5,"#21262D"],[1,G]],
                zmin=-1,zmax=1,text_auto=".2f",aspect="auto")
            fcm.update_layout(**PL,height=280,margin=dict(l=10,r=10,t=10,b=10),coloraxis_showscale=False)
            fcm.update_traces(textfont=dict(size=12,family="IBM Plex Mono"))
            st.plotly_chart(fcm,use_container_width=True)
        st.markdown('<div class="ibox" style="font-size:.8rem"><b>+1.0</b> move together · <b>0</b> no link · <b>−1.0</b> opposite</div>',unsafe_allow_html=True)
    with cc2:
        st.markdown('<div class="sec">30-Day Rolling Correlation vs EUA</div>',unsafe_allow_html=True)
        if "EUA (CO2.L)" in rdf.columns and len(rdf.columns)>1:
            frc=go.Figure()
            for i,col in enumerate(rdf.columns):
                if col=="EUA (CO2.L)": continue
                rc=rdf["EUA (CO2.L)"].rolling(30).corr(rdf[col])
                frc.add_trace(go.Scatter(x=rc.index,y=rc,name=col,line=dict(color=PAL[(i+1)%len(PAL)],width=2)))
            frc.add_hline(y=0,line_color=GR,line_dash="dot",opacity=.5)
            frc.add_hrect(y0=.5,y1=1,fillcolor=G,opacity=.04)
            frc.add_hrect(y0=-1,y1=-.5,fillcolor=R,opacity=.04)
            frc.update_layout(**PL,height=280,yaxis=dict(range=[-1,1],title="Correlation"),legend=dict(orientation="h",y=1.1))
            st.plotly_chart(frc,use_container_width=True)
    others=[c for c in rdf.columns if c!="EUA (CO2.L)"]
    if others and "EUA (CO2.L)" in rdf.columns:
        st.markdown('<div class="sec">Scatter Analysis — Daily Returns</div>',unsafe_allow_html=True)
        sc_cols=st.columns(len(others))
        for i,asset in enumerate(others):
            with sc_cols[i]:
                sub=rdf[["EUA (CO2.L)",asset]].dropna()*100
                cv=sub.corr().iloc[0,1]
                fsc=px.scatter(sub,x=asset,y="EUA (CO2.L)",trendline="ols",
                    labels={"EUA (CO2.L)":"EUA (%)"},color_discrete_sequence=[B])
                fsc.update_traces(marker=dict(size=4,opacity=.5))
                fsc.update_layout(**PL,height=260,margin=dict(l=30,r=10,t=40,b=30),
                    title=dict(text=f"EUA vs {asset}  r={cv:.2f}",font=dict(size=12,color=GR)))
                st.plotly_chart(fsc,use_container_width=True)
    st.markdown('<div class="wbox">⚠️ <b>Disclaimer:</b> Educational purposes only. Not investment advice.</div>',unsafe_allow_html=True)