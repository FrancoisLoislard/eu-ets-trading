"""
dashboard/app.py
================
Dashboard Streamlit pour le suivi du marché EUA (EU Carbon Allowances).

Lancement :
    streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Configuration de la page ──────────────────────────────────────────────────
st.set_page_config(
    page_title="EU-ETS Trading Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personnalisé ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1A7A4A;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1rem;
        color: #666;
        margin-top: 0;
    }
    .metric-card {
        background: #f8f9fa;
        border-left: 4px solid #1A7A4A;
        padding: 12px 16px;
        border-radius: 4px;
    }
    .stMetric label { font-size: 0.8rem !important; color: #555 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  FONCTIONS DE CHARGEMENT DES DONNÉES
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)  # Cache 1 heure — ne re-télécharge pas à chaque refresh
def load_price_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    """
    Télécharge les données de prix depuis Yahoo Finance.
    
    Le décorateur @st.cache_data mémorise le résultat :
    si vous rechargez la page dans l'heure, les données
    viennent du cache (pas d'appel réseau → plus rapide).
    """
    try:
        data = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        if data.empty:
            return pd.DataFrame()
        # Aplatir les colonnes multi-index si nécessaire
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        st.warning(f"Impossible de charger {ticker} : {e}")
        return pd.DataFrame()


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule les indicateurs techniques sur les prix de clôture."""
    if df.empty or "Close" not in df.columns:
        return df

    close = df["Close"]

    # Moyennes mobiles
    df["EMA_20"]  = close.ewm(span=20,  adjust=False).mean()
    df["EMA_50"]  = close.ewm(span=50,  adjust=False).mean()
    df["SMA_200"] = close.rolling(200).mean()

    # RSI (14 jours)
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    sma20       = close.rolling(20).mean()
    std20       = close.rolling(20).std()
    df["BB_upper"] = sma20 + 2 * std20
    df["BB_lower"] = sma20 - 2 * std20
    df["BB_mid"]   = sma20

    # Rendements
    df["Return_1d"] = close.pct_change()
    df["Return_5d"] = close.pct_change(5)
    df["Vol_20d"]   = df["Return_1d"].rolling(20).std() * np.sqrt(252)  # Volatilité annualisée

    return df


def get_seasonal_bias(month: int) -> tuple[str, str]:
    """Retourne le biais saisonnier historique pour un mois donné."""
    bias_map = {
        1:  ("+",    "Neutre/Haussier",  "#FFF9C4"),
        2:  ("++",   "Haussier",         "#C8E6C9"),
        3:  ("+++",  "Très Haussier",    "#A5D6A7"),
        4:  ("++++", "Fortement Haussier","#66BB6A"),
        5:  ("----", "Très Baissier",    "#FFCDD2"),
        6:  ("--",   "Baissier",         "#FFCDD2"),
        7:  ("-",    "Légèrement Baissier","#FFF9C4"),
        8:  ("=",    "Neutre",           "#F5F5F5"),
        9:  ("+",    "Légèrement Haussier","#F5F5F5"),
        10: ("+",    "Neutre/Haussier",  "#FFF9C4"),
        11: ("++",   "Haussier",         "#C8E6C9"),
        12: ("+++",  "Très Haussier",    "#A5D6A7"),
    }
    arrows, label, color = bias_map.get(month, ("=", "Neutre", "#F5F5F5"))
    return label, color


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ⚙️ Paramètres")
    st.markdown("---")

    period = st.selectbox(
        "Période d'analyse",
        options=["6mo", "1y", "2y", "5y"],
        index=2,
        format_func=lambda x: {"6mo": "6 mois", "1y": "1 an", "2y": "2 ans", "5y": "5 ans"}[x],
    )

    show_ema     = st.checkbox("Afficher EMA 20/50",    value=True)
    show_bb      = st.checkbox("Afficher Bollinger Bands", value=True)
    show_volume  = st.checkbox("Afficher les volumes",  value=True)
    show_rsi     = st.checkbox("Afficher le RSI",       value=True)
    show_corr    = st.checkbox("Afficher corrélations énergie", value=True)

    st.markdown("---")
    st.markdown("### 📡 Tickers surveillés")
    st.markdown("""
    | Actif | Ticker |
    |-------|--------|
    | EUA   | `CO2.L` |
    | Gas TTF | `TTF=F` |
    | Brent | `BZ=F` |
    | EuroStoxx | `^STOXX50E` |
    """)

    st.markdown("---")
    if st.button("🔄 Rafraîchir les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"*Mise à jour : {datetime.now().strftime('%H:%M:%S')}*")


# ══════════════════════════════════════════════════════════════════════════════
#  EN-TÊTE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<p class="main-title">🌍 EU-ETS Trading Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">European Union Allowances (EUA) — Analyse de marché en temps réel</p>', unsafe_allow_html=True)
st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
#  CHARGEMENT DES DONNÉES
# ══════════════════════════════════════════════════════════════════════════════

with st.spinner("Chargement des données depuis Yahoo Finance..."):
    df_eua   = load_price_data("CO2.L",    period=period)
    df_gas   = load_price_data("TTF=F",    period=period)
    df_brent = load_price_data("BZ=F",     period=period)
    df_stoxx = load_price_data("^STOXX50E", period=period)

# Vérifie qu'on a des données EUA
if df_eua.empty:
    st.error("""
    ❌ Impossible de charger les données EUA (CO2.L).
    
    Causes possibles :
    - Pas de connexion internet
    - Yahoo Finance temporairement indisponible
    
    Essayez de rafraîchir dans quelques minutes.
    """)
    st.stop()

# Calcul des indicateurs
df_eua = compute_indicators(df_eua)


# ══════════════════════════════════════════════════════════════════════════════
#  MÉTRIQUES CLÉS (ligne du haut)
# ══════════════════════════════════════════════════════════════════════════════

latest       = float(df_eua["Close"].iloc[-1])
prev         = float(df_eua["Close"].iloc[-2])
change_1d    = (latest - prev) / prev * 100
change_5d    = float(df_eua["Return_5d"].iloc[-1]) * 100
vol_20d      = float(df_eua["Vol_20d"].iloc[-1]) * 100
rsi_val      = float(df_eua["RSI"].iloc[-1])
high_52w     = float(df_eua["Close"].rolling(252).max().iloc[-1])
low_52w      = float(df_eua["Close"].rolling(252).min().iloc[-1])
current_month = datetime.now().month
seasonal_label, seasonal_color = get_seasonal_bias(current_month)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="💶 Prix EUA (€/tCO₂)",
        value=f"€{latest:.2f}",
        delta=f"{change_1d:+.2f}% aujourd'hui",
    )
with col2:
    st.metric(
        label="📅 Variation 5 jours",
        value=f"{change_5d:+.2f}%",
        delta=f"vs semaine dernière",
    )
with col3:
    st.metric(
        label="📊 Volatilité 20j (ann.)",
        value=f"{vol_20d:.1f}%",
        delta=None,
    )
with col4:
    rsi_status = "Suracheté 🔴" if rsi_val > 70 else ("Survendu 🟢" if rsi_val < 30 else "Neutre ⚪")
    st.metric(
        label="📈 RSI (14j)",
        value=f"{rsi_val:.1f}",
        delta=rsi_status,
    )
with col5:
    st.metric(
        label="📆 Biais saisonnier",
        value=seasonal_label,
        delta=f"Mois {current_month}",
    )

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
#  GRAPHIQUE PRINCIPAL EUA
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("📈 Prix EUA (CO2.L) — Analyse technique")

# Construction du graphique avec sous-graphiques
n_rows = 1 + int(show_volume) + int(show_rsi)
row_heights = [0.6] + [0.2] * (n_rows - 1)

fig = make_subplots(
    rows=n_rows, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.04,
    row_heights=row_heights,
)

current_row = 1

# ── Candlestick ──────────────────────────────────────────────────────────────
if all(c in df_eua.columns for c in ["Open", "High", "Low", "Close"]):
    fig.add_trace(go.Candlestick(
        x=df_eua.index,
        open=df_eua["Open"],  high=df_eua["High"],
        low=df_eua["Low"],    close=df_eua["Close"],
        name="EUA", increasing_line_color="#26A69A", decreasing_line_color="#EF5350",
    ), row=current_row, col=1)

# ── EMA ────────────────────────────────────────────────────────────────────
if show_ema and "EMA_20" in df_eua.columns:
    fig.add_trace(go.Scatter(
        x=df_eua.index, y=df_eua["EMA_20"],
        name="EMA 20", line=dict(color="#FF9800", width=1.5),
    ), row=current_row, col=1)
    fig.add_trace(go.Scatter(
        x=df_eua.index, y=df_eua["EMA_50"],
        name="EMA 50", line=dict(color="#2196F3", width=1.5),
    ), row=current_row, col=1)

# ── Bollinger Bands ───────────────────────────────────────────────────────────
if show_bb and "BB_upper" in df_eua.columns:
    fig.add_trace(go.Scatter(
        x=df_eua.index, y=df_eua["BB_upper"],
        name="BB Sup", line=dict(color="rgba(150,150,150,0.5)", width=1, dash="dot"),
    ), row=current_row, col=1)
    fig.add_trace(go.Scatter(
        x=df_eua.index, y=df_eua["BB_lower"],
        name="BB Inf", line=dict(color="rgba(150,150,150,0.5)", width=1, dash="dot"),
        fill="tonexty", fillcolor="rgba(150,150,150,0.05)",
    ), row=current_row, col=1)

# ── Volumes ────────────────────────────────────────────────────────────────
if show_volume and "Volume" in df_eua.columns:
    current_row += 1
    colors = ["#26A69A" if r >= 0 else "#EF5350" for r in df_eua["Return_1d"].fillna(0)]
    fig.add_trace(go.Bar(
        x=df_eua.index, y=df_eua["Volume"],
        name="Volume", marker_color=colors, showlegend=False,
    ), row=current_row, col=1)
    fig.update_yaxes(title_text="Volume", row=current_row, col=1)

# ── RSI ────────────────────────────────────────────────────────────────────
if show_rsi and "RSI" in df_eua.columns:
    current_row += 1
    fig.add_trace(go.Scatter(
        x=df_eua.index, y=df_eua["RSI"],
        name="RSI", line=dict(color="#9C27B0", width=1.5),
    ), row=current_row, col=1)
    # Zones de surachat/survente
    fig.add_hline(y=70, line_dash="dash", line_color="red",   opacity=0.5, row=current_row, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=current_row, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=current_row, col=1)

fig.update_layout(
    height=600,
    xaxis_rangeslider_visible=False,
    plot_bgcolor="white",
    paper_bgcolor="white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=40, b=40),
)
fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")

st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  CORRÉLATIONS AVEC LES MARCHÉS ÉNERGIE
# ══════════════════════════════════════════════════════════════════════════════

if show_corr:
    st.markdown("---")
    st.subheader("🔗 Corrélations EUA avec les marchés énergie")
    st.caption("Une corrélation proche de +1 signifie que les actifs bougent ensemble. Proche de -1 : ils bougent en sens opposé.")

    # Construire un DataFrame des rendements communs
    returns_dict = {"EUA": df_eua["Return_1d"].dropna()}
    if not df_gas.empty   and "Close" in df_gas.columns:
        returns_dict["Gas TTF"] = df_gas["Close"].pct_change().dropna()
    if not df_brent.empty and "Close" in df_brent.columns:
        returns_dict["Brent"]   = df_brent["Close"].pct_change().dropna()
    if not df_stoxx.empty and "Close" in df_stoxx.columns:
        returns_dict["EuroStoxx"] = df_stoxx["Close"].pct_change().dropna()

    if len(returns_dict) > 1:
        returns_df = pd.DataFrame(returns_dict).dropna()
        corr_matrix = returns_df.corr()

        col_heat, col_chart = st.columns([1, 2])

        with col_heat:
            st.markdown("**Matrice de corrélation (60 derniers jours)**")
            corr_60 = returns_df.tail(60).corr()
            fig_corr = px.imshow(
                corr_60,
                color_continuous_scale="RdYlGn",
                zmin=-1, zmax=1,
                text_auto=".2f",
                aspect="auto",
            )
            fig_corr.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_corr, use_container_width=True)

        with col_chart:
            st.markdown("**Corrélation glissante EUA / Gas TTF (30 jours)**")
            if "Gas TTF" in returns_df.columns:
                rolling_corr = returns_df["EUA"].rolling(30).corr(returns_df["Gas TTF"])
                fig_rc = go.Figure()
                fig_rc.add_trace(go.Scatter(
                    x=rolling_corr.index, y=rolling_corr,
                    fill="tozeroy", line=dict(color="#1A7A4A"),
                    fillcolor="rgba(26,122,74,0.15)", name="Corrélation 30j",
                ))
                fig_rc.add_hline(y=0, line_color="grey", line_dash="dash")
                fig_rc.update_layout(
                    height=280,
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=10, r=10, t=10, b=10),
                    yaxis=dict(range=[-1, 1], tickformat=".1f"),
                )
                st.plotly_chart(fig_rc, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  CONTEXTE DE MARCHÉ + SAISONNALITÉ
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
col_season, col_context = st.columns([1, 2])

with col_season:
    st.subheader("📅 Saisonnalité EU-ETS")
    months = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
    bias_scores = [0.3, 0.4, 0.6, 0.8, -0.5, -0.2, -0.1, 0.0, 0.2, 0.3, 0.4, 0.5]
    colors_bar  = ["#66BB6A" if b > 0 else ("#EF5350" if b < 0 else "#BDBDBD") for b in bias_scores]

    fig_season = go.Figure(go.Bar(
        x=months, y=bias_scores,
        marker_color=colors_bar,
        text=[f"{b:+.1f}" for b in bias_scores],
        textposition="outside",
    ))
    fig_season.add_vline(
        x=current_month - 1.5,
        line_color="orange", line_width=3,
        annotation_text="Maintenant", annotation_position="top",
    )
    fig_season.update_layout(
        height=280,
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=30, b=10),
        yaxis=dict(title="Biais historique", range=[-0.8, 1.1]),
        showlegend=False,
    )
    st.plotly_chart(fig_season, use_container_width=True)

with col_context:
    st.subheader("📋 Contexte du marché EUA")
    st.markdown("""
    **🏭 Mécanisme EU-ETS en bref**

    Chaque installation industrielle (acier, ciment, énergie...) doit remettre
    **1 EUA par tonne de CO₂ émise** avant le **30 avril** de chaque année.
    
    Les EUA peuvent être achetés aux enchères (ICE/EEX) ou sur le marché secondaire.
    
    ---
    
    **⚡ Principaux moteurs du prix EUA**

    | Facteur | Impact |
    |---------|--------|
    | Prix du gaz (TTF) ↑ | EUA ↑ (fuel switch vers charbon) |
    | Prix du charbon ↑ | EUA ↓ (fuel switch vers gaz) |
    | Températures froides | EUA ↑ (consommation énergie ↑) |
    | Croissance industrielle | EUA ↑ (production ↑ → émissions ↑) |
    | Annonces réglementaires | Volatilité forte dans les 2 sens |
    | MSR (Market Stability Reserve) | EUA ↑ (absorption des surplus) |
    
    ---
    
    **📌 Prochaine échéance réglementaire**  
    Deadline compliance annuelle : **30 avril**
    """)


# ══════════════════════════════════════════════════════════════════════════════
#  DONNÉES BRUTES (optionnel)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
with st.expander("🔍 Voir les données brutes (30 derniers jours)"):
    cols_to_show = [c for c in ["Close", "Volume", "EMA_20", "EMA_50", "RSI", "Vol_20d"] if c in df_eua.columns]
    df_display = df_eua[cols_to_show].tail(30).round(3).sort_index(ascending=False)
    df_display.index = df_display.index.strftime("%Y-%m-%d")
    st.dataframe(df_display, use_container_width=True)

st.caption("⚠️ Ce dashboard est à titre éducatif uniquement. Pas un conseil en investissement.")
