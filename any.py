"""
SkyCity Auckland Restaurants & Bars — Multi-Channel Profitability Intelligence
================================================================================
A Streamlit dashboard comparing In-Store, Uber Eats, DoorDash and Self-Delivery
channel economics: net profit, margins, commission drag, and what-if simulation.

Run locally:
    streamlit run app.py

Deploy free on Streamlit Community Cloud:
    1. Push this repo to GitHub
    2. Go to https://share.streamlit.io -> New app -> point to app/app.py
    3. Done — no secrets required, data.csv ships with the repo
"""

import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="SkyCity Auckland | Channel Profitability Intelligence",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CHANNELS = ["InStore", "UberEats", "DoorDash", "SelfDelivery"]
CHANNEL_LABEL = {
    "InStore": "In-Store",
    "UberEats": "Uber Eats",
    "DoorDash": "DoorDash",
    "SelfDelivery": "Self-Delivery",
}
CHANNEL_COLOR = {
    "InStore": "#2EC4B6",
    "UberEats": "#06C167",
    "DoorDash": "#FF3D57",
    "SelfDelivery": "#FFB703",
}

# ----------------------------------------------------------------------------
# STYLE — attractive dark "control-room" theme with gradient background
# ----------------------------------------------------------------------------
def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Sora:wght@600;700;800&display=swap');

        html, body, [class*="css"]  { font-family: 'Manrope', sans-serif; }

        .stApp {
            background:
                radial-gradient(circle at 8% 8%, rgba(46,196,182,0.16), transparent 40%),
                radial-gradient(circle at 92% 15%, rgba(255,183,3,0.14), transparent 45%),
                radial-gradient(circle at 50% 100%, rgba(255,61,87,0.10), transparent 55%),
                linear-gradient(160deg, #0B1220 0%, #0E1730 45%, #0B1220 100%);
            background-attachment: fixed;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0B1220 0%, #101B34 100%);
            border-right: 1px solid rgba(255,255,255,0.06);
        }
        section[data-testid="stSidebar"] * { color: #E7ECF7 !important; }

        h1, h2, h3 { font-family: 'Sora', sans-serif !important; color: #F5F7FF !important; }
        p, span, label, div { color: #C9D2E8; }

        .hero {
            padding: 28px 32px;
            border-radius: 18px;
            background: linear-gradient(120deg, rgba(46,196,182,0.14), rgba(255,183,3,0.08));
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 20px 45px rgba(0,0,0,0.35);
            margin-bottom: 18px;
        }
        .hero h1 { font-size: 2.1rem; margin-bottom: 4px; }
        .hero p { font-size: 1.0rem; color: #AEB8D4 !important; margin: 0; }

        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.045);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 16px 18px 10px 18px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.25);
        }
        div[data-testid="stMetricLabel"] { color: #9AA6C4 !important; font-weight: 600; }
        div[data-testid="stMetricValue"] { color: #F5F7FF !important; font-family: 'Sora', sans-serif; }

        .section-card {
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 18px;
            padding: 20px 22px;
            margin-bottom: 18px;
            box-shadow: 0 14px 34px rgba(0,0,0,0.28);
        }

        .badge {
            display:inline-block; padding: 3px 12px; border-radius: 999px;
            font-size: 0.72rem; font-weight: 700; letter-spacing:.04em;
            background: rgba(46,196,182,0.18); color:#7FEFE2 !important; margin-right:6px;
        }
        .badge-warn { background: rgba(255,61,87,0.18); color:#FF9AAA !important; }
        .badge-gold { background: rgba(255,183,3,0.18); color:#FFDD8A !important; }

        [data-testid="stTabs"] button { color: #AEB8D4 !important; font-weight:600; }
        [data-testid="stTabs"] button[aria-selected="true"] { color: #FFFFFF !important; }

        hr { border-color: rgba(255,255,255,0.08); }
        .stDataFrame { border-radius: 12px; overflow: hidden; }
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


PLOTLY_TEMPLATE = "plotly_dark"


def style_fig(fig, height=420):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#E7ECF7", size=13),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=10, t=60, b=10),
        height=height,
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")
    return fig


# ----------------------------------------------------------------------------
# DATA LOADING + FEATURE ENGINEERING
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "..", "data", "restaurants.csv"),
        os.path.join(here, "data", "restaurants.csv"),
        os.path.join(here, "SkyCity_Auckland_Restaurants___Bars.csv"),
    ]
    path = next((c for c in candidates if os.path.exists(c)), candidates[0])
    df = pd.read_csv(path)

    # normalize expected column names (robust to minor renames)
    rename_map = {
        "InStoreOrdersCount": "InStoreOrders",
        "UberEatsOrdersCount": "UberEatsOrders",
        "DoorDashOrdersCount": "DoorDashOrders",
        "SelfDeliveryOrdersCount": "SelfDeliveryOrders",
        "DeliveryCostOrder": "DeliveryCostPerOrder",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    for ch in CHANNELS:
        rev, prof, ordc = f"{ch}Revenue", f"{ch}NetProfit", f"{ch}Orders"
        df[f"{ch}_PPO"] = np.where(df[ordc] > 0, df[prof] / df[ordc], np.nan)
        df[f"{ch}_Margin"] = np.where(df[rev] > 0, df[prof] / df[rev] * 100, np.nan)

    df["TotalRevenue"] = df[[f"{c}Revenue" for c in CHANNELS]].sum(axis=1)
    df["TotalProfit"] = df[[f"{c}NetProfit" for c in CHANNELS]].sum(axis=1)
    df["BlendedMargin"] = np.where(
        df["TotalRevenue"] > 0, df["TotalProfit"] / df["TotalRevenue"] * 100, np.nan
    )
    df["DeliveryRevenue"] = df["UberEatsRevenue"] + df["DoorDashRevenue"] + df["SelfDeliveryRevenue"]
    df["CommissionDrag$"] = (df["UberEatsRevenue"] * df["CommissionRate"]) + (
        df["DoorDashRevenue"] * df["CommissionRate"]
    )
    return df


df_raw = load_data()

# ----------------------------------------------------------------------------
# SIDEBAR — FILTERS + WHAT-IF CONTROLS
# ----------------------------------------------------------------------------
inject_css()

with st.sidebar:
    st.markdown("### 🍽️ SkyCity Auckland")
    st.caption("Multi-Channel Profitability Console")
    st.markdown("---")

    st.markdown("#### Filters")
    cuisines = st.multiselect(
        "Cuisine Type", sorted(df_raw["CuisineType"].unique()), default=[]
    )
    segments = st.multiselect(
        "Segment", sorted(df_raw["Segment"].unique()), default=[]
    )
    subregions = st.multiselect(
        "Subregion", sorted(df_raw["Subregion"].unique()), default=[]
    )
    restaurants = st.multiselect(
        "Restaurant (search)", sorted(df_raw["RestaurantName"].unique()), default=[]
    )

    st.markdown("---")
    st.markdown("#### ⚙️ What-If Simulator")
    st.caption("Stress-test commission & delivery cost assumptions")
    commission_delta = st.slider("Commission rate change (pp)", -10, 15, 0, 1,
                                  help="Applies to Uber Eats & DoorDash commission rate")
    delivery_cost_delta = st.slider("Self-delivery cost / order ($)", -2.0, 5.0, 0.0, 0.1)
    st.markdown("---")
    st.caption("Data: SkyCity Auckland Restaurants & Bars · Unified Mentor Capstone")

# apply filters
df = df_raw.copy()
if cuisines:
    df = df[df["CuisineType"].isin(cuisines)]
if segments:
    df = df[df["Segment"].isin(segments)]
if subregions:
    df = df[df["Subregion"].isin(subregions)]
if restaurants:
    df = df[df["RestaurantName"].isin(restaurants)]

if df.empty:
    st.warning("No restaurants match the current filters. Adjust filters in the sidebar.")
    st.stop()

# what-if adjusted profit (recomputed on the fly, non-destructive)
sim = df.copy()
new_comm = (sim["CommissionRate"] + commission_delta / 100).clip(0, 0.6)
sim["UberEatsNetProfit_sim"] = sim["UberEatsRevenue"] * (
    1 - sim["COGSRate"] - sim["OPEXRate"] - new_comm
)
sim["DoorDashNetProfit_sim"] = sim["DoorDashRevenue"] * (
    1 - sim["COGSRate"] - sim["OPEXRate"] - new_comm
)
new_dcost = (sim["DeliveryCostPerOrder"] + delivery_cost_delta).clip(lower=0)
sim["SD_DeliveryTotalCost_sim"] = sim["SelfDeliveryOrders"] * new_dcost
sim["SelfDeliveryNetProfit_sim"] = (
    sim["SelfDeliveryRevenue"] * (1 - sim["COGSRate"] - sim["OPEXRate"])
    - sim["SD_DeliveryTotalCost_sim"]
)
sim["InStoreNetProfit_sim"] = sim["InStoreNetProfit"]

# ----------------------------------------------------------------------------
# HERO
# ----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <h1>🍽️ SkyCity Auckland Channel Profitability Intelligence</h1>
      <p>Where orders come from is not the same question as where profit comes from.
      Compare In-Store, Uber Eats, DoorDash and Self-Delivery on true unit economics —
      not just revenue.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

n_rest = df["RestaurantID"].nunique()
st.caption(f"Showing **{n_rest}** restaurant branches · {len(df)} rows matching current filters")

# ----------------------------------------------------------------------------
# TOP KPI ROW
# ----------------------------------------------------------------------------
total_rev = df["TotalRevenue"].sum()
total_profit = df["TotalProfit"].sum()
blended_margin = total_profit / total_rev * 100 if total_rev else 0
commission_drag = df["CommissionDrag$"].sum()
best_channel = df[[f"{c}_Margin" for c in CHANNELS]].mean().idxmax().replace("_Margin", "")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Revenue", f"${total_rev:,.0f}")
c2.metric("Total Net Profit", f"${total_profit:,.0f}")
c3.metric("Blended Margin", f"{blended_margin:.1f}%")
c4.metric("Commission Paid to Aggregators", f"${commission_drag:,.0f}")
c5.metric("Most Margin-Efficient Channel", CHANNEL_LABEL[best_channel])

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------------
tab_overview, tab_channel, tab_cost, tab_cuisine, tab_whatif, tab_risk, tab_data = st.tabs(
    [
        "📊 Overview",
        "🔀 Channel Profitability",
        "🧱 Cost Breakdown",
        "🍜 Cuisine & Segment",
        "🎛️ What-If Simulator",
        "⚠️ Risk & Volatility",
        "🗂️ Data Explorer",
    ]
)

# ================= OVERVIEW =================
with tab_overview:
    colA, colB = st.columns([1.3, 1])
    with colA:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Revenue vs. Net Profit by Channel")
        rev_by_ch = [df[f"{c}Revenue"].sum() for c in CHANNELS]
        prof_by_ch = [df[f"{c}NetProfit"].sum() for c in CHANNELS]
        fig = go.Figure()
        fig.add_bar(
            name="Revenue", x=[CHANNEL_LABEL[c] for c in CHANNELS], y=rev_by_ch,
            marker_color="rgba(255,255,255,0.18)",
        )
        fig.add_bar(
            name="Net Profit", x=[CHANNEL_LABEL[c] for c in CHANNELS], y=prof_by_ch,
            marker_color=[CHANNEL_COLOR[c] for c in CHANNELS],
        )
        fig.update_layout(barmode="group", title="High revenue does not equal high profit")
        st.plotly_chart(style_fig(fig), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Order Volume Mix")
        ord_by_ch = [df[f"{c}Orders"].sum() for c in CHANNELS]
        fig = px.pie(
            names=[CHANNEL_LABEL[c] for c in CHANNELS], values=ord_by_ch, hole=0.55,
            color=[CHANNEL_LABEL[c] for c in CHANNELS],
            color_discrete_map={CHANNEL_LABEL[c]: CHANNEL_COLOR[c] for c in CHANNELS},
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(style_fig(fig, height=420), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Margin % by Channel — the real story")
    margins = [df[f"{c}NetProfit"].sum() / df[f"{c}Revenue"].sum() * 100 if df[f"{c}Revenue"].sum() else 0 for c in CHANNELS]
    fig = go.Figure(go.Bar(
        x=[CHANNEL_LABEL[c] for c in CHANNELS], y=margins,
        marker_color=[CHANNEL_COLOR[c] for c in CHANNELS],
        text=[f"{m:.1f}%" for m in margins], textposition="outside",
    ))
    fig.update_layout(yaxis_title="Net Margin (%)")
    st.plotly_chart(style_fig(fig, height=380), use_container_width=True)
    ue_m, dd_m = margins[1], margins[2]
    st.markdown(
        f"""
        <span class="badge">In-Store {margins[0]:.1f}%</span>
        <span class="badge-warn badge">Uber Eats {ue_m:.1f}%</span>
        <span class="badge-warn badge">DoorDash {dd_m:.1f}%</span>
        <span class="badge-gold badge">Self-Delivery {margins[3]:.1f}%</span>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Aggregator channels (Uber Eats, DoorDash) often carry the highest order volume and "
        "revenue, yet their margins are compressed to near break-even by commission rates. "
        "In-Store and Self-Delivery retain far more of every revenue dollar as profit."
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ================= CHANNEL PROFITABILITY =================
with tab_channel:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Net Profit per Order (True Channel Efficiency)")
    ppo = [df[f"{c}_PPO"].mean() for c in CHANNELS]
    fig = go.Figure(go.Bar(
        x=[CHANNEL_LABEL[c] for c in CHANNELS], y=ppo,
        marker_color=[CHANNEL_COLOR[c] for c in CHANNELS],
        text=[f"${v:.2f}" for v in ppo], textposition="outside",
    ))
    fig.update_layout(yaxis_title="Avg. Net Profit per Order ($)")
    st.plotly_chart(style_fig(fig, height=400), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Absolute Profit vs. Margin Efficiency")
        scat = pd.DataFrame({
            "Channel": [CHANNEL_LABEL[c] for c in CHANNELS],
            "TotalProfit": prof_by_ch if 'prof_by_ch' in dir() else [df[f"{c}NetProfit"].sum() for c in CHANNELS],
            "Margin%": [df[f"{c}NetProfit"].sum() / df[f"{c}Revenue"].sum() * 100 if df[f"{c}Revenue"].sum() else 0 for c in CHANNELS],
        })
        fig = px.scatter(
            scat, x="Margin%", y="TotalProfit", text="Channel", size="TotalProfit",
            color="Channel", color_discrete_map={CHANNEL_LABEL[c]: CHANNEL_COLOR[c] for c in CHANNELS},
        )
        fig.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="white")))
        fig.update_layout(xaxis_title="Net Margin (%)", yaxis_title="Total Net Profit ($)", showlegend=False)
        st.plotly_chart(style_fig(fig, height=400), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Most Cost-Efficient Channel per Restaurant")
        margin_cols = [f"{c}_Margin" for c in CHANNELS]
        best = df[margin_cols].idxmax(axis=1).str.replace("_Margin", "", regex=False)
        counts = best.value_counts().reindex(CHANNELS).fillna(0)
        fig = go.Figure(go.Bar(
            x=[CHANNEL_LABEL[c] for c in CHANNELS], y=counts.values,
            marker_color=[CHANNEL_COLOR[c] for c in CHANNELS],
        ))
        fig.update_layout(yaxis_title="# Restaurants where channel is most efficient")
        st.plotly_chart(style_fig(fig, height=400), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ================= COST BREAKDOWN =================
with tab_cost:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Cost Waterfall — Revenue to Net Profit")
    channel_pick = st.selectbox("Select channel", CHANNELS, format_func=lambda c: CHANNEL_LABEL[c])
    rev = df[f"{channel_pick}Revenue"].sum()
    cogs = (df[f"{channel_pick}Revenue"] * df["COGSRate"]).sum()
    opex = (df[f"{channel_pick}Revenue"] * df["OPEXRate"]).sum()
    if channel_pick in ("UberEats", "DoorDash"):
        commission = (df[f"{channel_pick}Revenue"] * df["CommissionRate"]).sum()
        delivery_cost = 0
    elif channel_pick == "SelfDelivery":
        commission = 0
        delivery_cost = df["SD_DeliveryTotalCost"].sum()
    else:
        commission = 0
        delivery_cost = 0
    net = df[f"{channel_pick}NetProfit"].sum()

    measures = ["absolute", "relative", "relative", "relative", "relative", "total"]
    labels = ["Gross Revenue", "COGS", "OPEX", "Commission", "Delivery Cost", "Net Profit"]
    values = [rev, -cogs, -opex, -commission, -delivery_cost, net]
    fig = go.Figure(go.Waterfall(
        x=labels, measure=measures, y=values,
        decreasing=dict(marker=dict(color="#FF3D57")),
        increasing=dict(marker=dict(color="#2EC4B6")),
        totals=dict(marker=dict(color="#FFB703")),
        connector=dict(line=dict(color="rgba(255,255,255,0.25)")),
        text=[f"${v:,.0f}" for v in values],
    ))
    fig.update_layout(title=f"{CHANNEL_LABEL[channel_pick]} — Cost Waterfall")
    st.plotly_chart(style_fig(fig, height=460), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Commission Drag Index")
        st.caption("Revenue lost to aggregator commissions — Uber Eats vs DoorDash")
        drag = pd.DataFrame({
            "Channel": ["Uber Eats", "DoorDash"],
            "Commission $": [
                (df["UberEatsRevenue"] * df["CommissionRate"]).sum(),
                (df["DoorDashRevenue"] * df["CommissionRate"]).sum(),
            ],
        })
        fig = px.bar(drag, x="Channel", y="Commission $", color="Channel",
                     color_discrete_map={"Uber Eats": CHANNEL_COLOR["UberEats"], "DoorDash": CHANNEL_COLOR["DoorDash"]})
        st.plotly_chart(style_fig(fig, height=360), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Self-Delivery ROI Breakeven")
        st.caption("Net profit per order as delivery cost per order rises")
        cost_range = np.linspace(0, 8, 30)
        avg_rev_per_order = (df["SelfDeliveryRevenue"].sum() / df["SelfDeliveryOrders"].sum())
        avg_cogs_opex = (df["COGSRate"] + df["OPEXRate"]).mean()
        ppo_curve = avg_rev_per_order * (1 - avg_cogs_opex) - cost_range
        fig = go.Figure(go.Scatter(x=cost_range, y=ppo_curve, mode="lines", line=dict(color=CHANNEL_COLOR["SelfDelivery"], width=3)))
        fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.4)")
        fig.update_layout(xaxis_title="Delivery Cost per Order ($)", yaxis_title="Net Profit per Order ($)")
        st.plotly_chart(style_fig(fig, height=360), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ================= CUISINE & SEGMENT =================
with tab_cuisine:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Channel Margin Heatmap by Cuisine Type")
    heat = df.groupby("CuisineType")[[f"{c}_Margin" for c in CHANNELS]].mean()
    heat.columns = [CHANNEL_LABEL[c] for c in CHANNELS]
    fig = px.imshow(
        heat, text_auto=".1f", aspect="auto", color_continuous_scale="RdYlGn",
        labels=dict(color="Margin %"),
    )
    st.plotly_chart(style_fig(fig, height=420), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Channel Margin Heatmap by Segment")
        heat2 = df.groupby("Segment")[[f"{c}_Margin" for c in CHANNELS]].mean()
        heat2.columns = [CHANNEL_LABEL[c] for c in CHANNELS]
        fig = px.imshow(heat2, text_auto=".1f", aspect="auto", color_continuous_scale="RdYlGn", labels=dict(color="Margin %"))
        st.plotly_chart(style_fig(fig, height=380), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Blended Margin by Subregion")
        reg = df.groupby("Subregion").apply(
            lambda g: g["TotalProfit"].sum() / g["TotalRevenue"].sum() * 100 if g["TotalRevenue"].sum() else 0
        ).reset_index(name="BlendedMargin%")
        fig = px.bar(reg, x="Subregion", y="BlendedMargin%", color="BlendedMargin%", color_continuous_scale="Tealgrn")
        st.plotly_chart(style_fig(fig, height=380), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Margin-Resilient vs Margin-Fragile Cuisines (Blended)")
    resil = df.groupby("CuisineType").apply(
        lambda g: g["TotalProfit"].sum() / g["TotalRevenue"].sum() * 100 if g["TotalRevenue"].sum() else 0
    ).reset_index(name="BlendedMargin%").sort_values("BlendedMargin%", ascending=True)
    fig = px.bar(resil, x="BlendedMargin%", y="CuisineType", orientation="h", color="BlendedMargin%", color_continuous_scale="RdYlGn")
    st.plotly_chart(style_fig(fig, height=420), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ================= WHAT-IF =================
with tab_whatif:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("What-If: Adjusted Net Profit by Channel")
    st.caption(
        f"Commission change: **{commission_delta:+d}pp** · "
        f"Self-delivery cost change: **{delivery_cost_delta:+.1f}$/order** — set sliders in the sidebar."
    )
    base_vals = [df[f"{c}NetProfit"].sum() for c in CHANNELS]
    sim_vals = [
        sim["InStoreNetProfit_sim"].sum(),
        sim["UberEatsNetProfit_sim"].sum(),
        sim["DoorDashNetProfit_sim"].sum(),
        sim["SelfDeliveryNetProfit_sim"].sum(),
    ]
    fig = go.Figure()
    fig.add_bar(name="Current", x=[CHANNEL_LABEL[c] for c in CHANNELS], y=base_vals, marker_color="rgba(255,255,255,0.25)")
    fig.add_bar(name="Simulated", x=[CHANNEL_LABEL[c] for c in CHANNELS], y=sim_vals, marker_color=[CHANNEL_COLOR[c] for c in CHANNELS])
    fig.update_layout(barmode="group", yaxis_title="Net Profit ($)")
    st.plotly_chart(style_fig(fig, height=440), use_container_width=True)

    delta_total = sum(sim_vals) - sum(base_vals)
    color = "🟢" if delta_total >= 0 else "🔴"
    st.markdown(f"### {color} Net profit impact: **${delta_total:,.0f}**")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Commission Sensitivity Curve (Uber Eats & DoorDash combined)")
    deltas = np.arange(-10, 16, 1)
    profits = []
    for d in deltas:
        c = (df["CommissionRate"] + d / 100).clip(0, 0.6)
        ue = df["UberEatsRevenue"] * (1 - df["COGSRate"] - df["OPEXRate"] - c)
        dd = df["DoorDashRevenue"] * (1 - df["COGSRate"] - df["OPEXRate"] - c)
        profits.append((ue + dd).sum())
    fig = go.Figure(go.Scatter(x=deltas, y=profits, mode="lines+markers", line=dict(color="#06C167", width=3)))
    fig.add_vline(x=commission_delta, line_dash="dash", line_color="#FFB703")
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.35)")
    fig.update_layout(xaxis_title="Commission Rate Change (pp)", yaxis_title="Combined Aggregator Net Profit ($)")
    st.plotly_chart(style_fig(fig, height=400), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ================= RISK & VOLATILITY =================
with tab_risk:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Profit Volatility Score by Channel (Coefficient of Variation)")
    vol = {}
    for c in CHANNELS:
        m, s = df[f"{c}_Margin"].mean(), df[f"{c}_Margin"].std()
        vol[CHANNEL_LABEL[c]] = abs(s / m) if m else np.nan
    volser = pd.Series(vol).sort_values(ascending=False)
    fig = go.Figure(go.Bar(x=volser.index, y=volser.values,
                            marker_color=[CHANNEL_COLOR[c] for c in CHANNELS]))
    fig.update_layout(yaxis_title="Volatility Score (lower = more stable)")
    st.plotly_chart(style_fig(fig, height=400), use_container_width=True)
    st.caption("Higher scores indicate margins that swing widely across restaurants — a sign of inconsistent, harder-to-forecast channel economics.")
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Margin Distribution by Channel")
        long = pd.concat([
            pd.DataFrame({"Channel": CHANNEL_LABEL[c], "Margin%": df[f"{c}_Margin"]}) for c in CHANNELS
        ])
        fig = px.box(long, x="Channel", y="Margin%", color="Channel",
                     color_discrete_map={CHANNEL_LABEL[c]: CHANNEL_COLOR[c] for c in CHANNELS})
        st.plotly_chart(style_fig(fig, height=420), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Loss-Prone Restaurants (Negative Margin Count)")
        loss_counts = {}
        for c in CHANNELS:
            loss_counts[CHANNEL_LABEL[c]] = int((df[f"{c}_Margin"] < 0).sum())
        lc = pd.Series(loss_counts).sort_values(ascending=False)
        fig = go.Figure(go.Bar(x=lc.index, y=lc.values, marker_color=[CHANNEL_COLOR[c] for c in CHANNELS]))
        fig.update_layout(yaxis_title="# Restaurant-branches with negative margin")
        st.plotly_chart(style_fig(fig, height=420), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ================= DATA EXPLORER =================
with tab_data:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Restaurant-Level Data")
    show_cols = [
        "RestaurantName", "CuisineType", "Segment", "Subregion", "MonthlyOrders",
        "TotalRevenue", "TotalProfit", "BlendedMargin",
        "InStore_Margin", "UberEats_Margin", "DoorDash_Margin", "SelfDelivery_Margin",
    ]
    st.dataframe(
        df[show_cols].round(2).sort_values("TotalProfit", ascending=False),
        use_container_width=True, height=480,
    )
    csv = df[show_cols].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download filtered data as CSV", csv, "skycity_filtered.csv", "text/csv")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div style="text-align:center; padding: 18px 0 6px 0; color:#7A87AC; font-size:0.82rem;">
      SkyCity Auckland Restaurants & Bars · Multi-Channel Profitability Intelligence ·
      Built with Streamlit + Plotly
    </div>
    """,
    unsafe_allow_html=True,
)
