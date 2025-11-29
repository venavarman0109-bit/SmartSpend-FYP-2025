#Author : Sharvena A/P Kumaran
#Student ID : 0128131
#FYP PROJECT 2025 UNIVERSITY OF WOLLONGONG MALAYSIA
# analysis_page.py
import base64
import os
from typing import Optional
import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet

# Reuse existing helpers
from money_magic_page_file import get_conn, ensure_base_schema, get_income
from moneymap_page import init_schema as init_money_map_schema

# ============================================================
#   BACKGROUND & GLOBAL STYLE
# ============================================================
BG_PATH = r"C:\Users\sharv\Downloads\UOW\FYP\FYP2\Analysis page bg.jpg"
LOGO_PATH = r"C:/Users/sharv/Downloads/UOW/FYP/FYP2/smartspend_logo.png"


def _encode_local_image_to_base64(path: str) -> Optional[str]:
    try:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    return None


def apply_bg():
    # --- Load Background ---
    b64 = _encode_local_image_to_base64(BG_PATH)

    # --- BACKGROUND CSS ---
    bg_style = ""
    if b64:
        bg_style = f"""
            .stApp {{
                background: url("data:image/jpeg;base64,{b64}") no-repeat center center fixed;
                background-size: cover;
            }}
        """

    st.markdown(
        f"""
        <style>
            {bg_style}

            /* ======================
               BUTTONS STYLING
            ======================= */
            div.stButton>button {{
                background: linear-gradient(to right,#ffffba,#baffc9,#bae1ff);
                color:#003366;
                border:none;
                border-radius:8px;
                padding:0.6em 1.5em;
                font-weight: 800 !important;
                letter-spacing: 0.3px;
                font-size:16px;
                cursor:pointer;
                transition:0.3s ease;
            }}
            div.stButton>button:hover {{
                filter:brightness(1.05);
                transform:scale(1.03);
            }}

            /* ======================
               INFO CARDS
            ======================= */
            .mm-card {{
                background:rgba(252,243,187,0.95);
                border-radius:14px;
                padding:14px 18px;
                box-shadow:0 3px 8px rgba(0,0,0,0.15);
                margin-bottom:10px;
            }}
            .mm-card-title {{
                color:#003366;
                font-weight:900;
                font-size:12px;
                margin-bottom:6px;
            }}
            .mm-card-value {{
                font-size:16px;
                font-weight:700;
                color:#1a4b82;
            }}

            /* ======================
               SCROLLING TABLE
            ======================= */
            .scroll-table {{
                overflow-y:auto;
                max-height:420px;
                background:rgba(255,255,255,0.95);
                border-radius:10px;
                padding:10px;
                box-shadow:0 4px 8px rgba(0,0,0,0.15);
            }}

            /* ======================
               INSIGHT CARD
            ======================= */
            .insight-card {{
                background: rgba(255, 249, 196, 0.9);
                border-left: 6px solid #f4d03f;
                padding: 18px 22px;
                border-radius: 12px;
                box-shadow: 0 3px 8px rgba(0,0,0,0.12);
                margin-top: 10px;
                margin-bottom: 18px;
            }}
            .insight-card ul {{
                margin-left: 0;
                padding-left: 20px;
            }}
            .insight-card li {{
                margin-bottom: 8px;
                font-size: 15px;
            }}

            /* ======================
               KPI CARDS
            ======================= */
            .kpi-strip {{
                display:flex;
                gap:16px;
                flex-wrap:wrap;
                margin-top:10px;
                margin-bottom:4px;
            }}
            .kpi-card {{
                flex:1 1 220px;
                background:rgba(255,255,255,0.97);
                border-radius:18px;
                padding:14px 18px;
                box-shadow:0 3px 10px rgba(0,0,0,0.15);
                position:relative;
                overflow:hidden;
            }}
            .kpi-title {{
                font-size:13px;
                font-weight:600;
                color:#555;
                margin-bottom:4px;
            }}
            .kpi-value {{
                font-size:22px;
                font-weight:800;
                color:#003366;
                margin-bottom:4px;
            }}
            .kpi-sub {{
                font-size:12px;
                color:#666;
            }}

            .kpi-good {{
                border:1px solid #4caf50;
                animation:pulseGreen 2.4s infinite;
            }}
            .kpi-medium {{
                border:1px solid #ffc107;
                animation:pulseAmber 2.4s infinite;
            }}
            .kpi-bad {{
                border:1px solid #f44336;
                animation:pulseRed 2.4s infinite;
            }}

            @keyframes pulseGreen {{
                0% {{ box-shadow:0 0 0 0 rgba(76,175,80,0.65); }}
                70% {{ box-shadow:0 0 0 14px rgba(76,175,80,0); }}
                100% {{ box-shadow:0 0 0 0 rgba(76,175,80,0); }}
            }}
            @keyframes pulseAmber {{
                0% {{ box-shadow:0 0 0 0 rgba(255,193,7,0.65); }}
                70% {{ box-shadow:0 0 0 14px rgba(255,193,7,0); }}
                100% {{ box-shadow:0 0 0 0 rgba(255,193,7,0); }}
            }}
            @keyframes pulseRed {{
                0% {{ box-shadow:0 0 0 0 rgba(244,67,54,0.65); }}
                70% {{ box-shadow:0 0 0 14px rgba(244,67,54,0); }}
                100% {{ box-shadow:0 0 0 0 rgba(244,67,54,0); }}
            }}
        </style>
        <div class="blur-overlay"></div>
        """,
        unsafe_allow_html=True,
    )

    expander_style = """
            /* Expander styling */
            div[data-testid="stExpander"]{
                background: rgba(143,235,250,0.98) !important;
                border: 1px solid #e6e6e6 !important;
                border-radius: 12px !important;
                box-shadow: 0 3px 10px rgba(0,0,0,0.08) !important;
                margin: 10px 0 12px 0 !important;
            }
            div[data-testid="stExpander"] > details > summary{
                background: linear-gradient(to right, #07889C, #27DAF5) !important;
                color: white !important;
                padding: 14px 18px !important;
                font-weight: bold !important;
                font-size: 30px !important;
                border-radius: 12px !important;
            }
            div[data-testid="stExpander"] > details > div{
                background: rgba(231,251,254,1.0) !important;
                border-top: 1px solid #eee !important;
                padding: 14px 18px 18px 18px !important;
                border-bottom-left-radius: 12px !important;
                border-bottom-right-radius: 12px !important;
            }
        """

    st.markdown(
        f"""
            <style>
                {bg_style}
                {expander_style}
            </style>
            """,
        unsafe_allow_html=True,
    )


# ============================================================
#   SCHEMA ENSURE
# ============================================================
def ensure_analytics_schema():
    """
    Make sure all base tables exist.
    Uses MoneyMagic + MoneyMap initialisations.
    """
    ensure_base_schema()
    init_money_map_schema()


# ============================================================
#   DATA LOADERS
# ============================================================
@st.cache_data
def load_budget_df(user_id: int) -> pd.DataFrame:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(money_magic_budget);")
    cols = [c[1] for c in cur.fetchall()]

    col_map = {
        "category": "Category",
        "item_name": "Item",
        "estimated_amount": "Estimated (RM)",
        "actual_amount": "Actual (RM)",
        "envelope_balance": "Envelope (RM)",
        "payment_progress": "Payment Progress",
        "status": "Status",
        "created_at": "Created",
    }

    select_cols = []
    for c_raw, c_alias in col_map.items():
        if c_raw in cols:
            select_cols.append(f"{c_raw} AS '{c_alias}'")

    if "confirmed" in cols:
        select_cols.append("confirmed AS 'Confirmed'")

    if not select_cols:
        conn.close()
        return pd.DataFrame()

    query = "SELECT " + ", ".join(select_cols) + " FROM money_magic_budget WHERE user_id = ?;"
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()

    if "Confirmed" not in df.columns:
        df["Confirmed"] = 0

    for c in ["Estimated (RM)", "Actual (RM)", "Envelope (RM)"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    if "Status" in df.columns:
        df["Status"] = df["Status"].fillna("Pending")

    return df


def load_transactions_df(user_id: int) -> pd.DataFrame:
    conn = get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY date;",
            conn,
            params=(user_id,),
        )
    except Exception:
        df = pd.DataFrame()

    conn.close()

    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


# ============================================================
#   SMALL HELPERS
# ============================================================
def _format_rm(x: float) -> str:
    return f"RM {x:,.2f}"

def get_income(user_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT monthly_income 
        FROM money_magic_income 
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1;
    """, (user_id,))

    row = cur.fetchone()
    conn.close()

    if row:
        return float(row[0])
    return 0.0

def _summary_cards(df: pd.DataFrame, income: float):
    if df.empty:
        st.info("No budget data available yet. Please configure your budget in MoneyMagic.")
        return

    total_est = float(df["Estimated (RM)"].sum()) if "Estimated (RM)" in df.columns else 0.0
    total_act = float(df["Actual (RM)"].sum()) if "Actual (RM)" in df.columns else 0.0
    total_env = float(df["Envelope (RM)"].sum()) if "Envelope (RM)" in df.columns else 0.0
    remaining_income = float(income - total_act)
    exceeded_count = int(((df.get("Actual (RM)", 0) > df.get("Estimated (RM)", 0))).sum())
    active_count = int((df.get("Status", pd.Series([])) == "Active").sum())
    completed_count = int((df.get("Status", pd.Series([])) == "Completed").sum())
    diff = total_est - total_act

    st.markdown(
        "<h2 style='color:#003366; text-align:left;'>🔍 Budget Snapshot</h2>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="mm-card">
              <div class="mm-card-title">Total Estimated</div>
              <div class="mm-card-value">{_format_rm(total_est)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="mm-card">
              <div class="mm-card-title">Total Actual</div>
              <div class="mm-card-value">{_format_rm(total_act)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="mm-card">
              <div class="mm-card-title">Envelope Balance</div>
              <div class="mm-card-value">{_format_rm(total_env)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        color = "#1db954" if diff >= 0 else "#e53935"
        st.markdown(
            f"""
            <div class="mm-card">
              <div class="mm-card-title">Difference(Est-Actual)</div>
              <div class="mm-card-value" style="color:{color};">{_format_rm(diff)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        color = "#1db954" if remaining_income >= 0 else "#e53935"
        st.markdown(
            f"""
            <div class="mm-card">
              <div class="mm-card-title">Remaining Income</div>
              <div class="mm-card-value" style="color:{color};">{_format_rm(remaining_income)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            f"""
            <div class="mm-card">
              <div class="mm-card-title">Exceeded Items</div>
              <div class="mm-card-value" style="color:#e53935;">{exceeded_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c7:
        st.markdown(
            f"""
            <div class="mm-card">
              <div class="mm-card-title">Active Items</div>
              <div class="mm-card-value" style="color:#ffa000;">{active_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c8:
        st.markdown(
            f"""
            <div class="mm-card">
              <div class="mm-card-title">Completed Items</div>
              <div class="mm-card-value" style="color:#43a047;">{completed_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
#   CHARTS
# ============================================================
def _category_comparison_chart(df_budget: pd.DataFrame):
    """
    Side-by-side bar charts comparing Estimated, Actual, and Envelope
    for each selected category.
    """
    if df_budget.empty:
        st.info("No budget data available yet.")
        return

    # Use only numeric columns that actually exist
    value_cols = [c for c in ["Estimated (RM)", "Actual (RM)", "Envelope (RM)"] if c in df_budget.columns]
    if "Category" not in df_budget.columns or len(value_cols) == 0:
        st.info("Not enough data columns to build this chart.")
        return

    melted_data = df_budget.melt(
        id_vars="Category",
        value_vars=value_cols,
        var_name="Type",
        value_name="Amount",
    )

    categories = melted_data["Category"].unique()

    for category in categories:
        with st.expander(f"{category} Budget vs Actual vs Envelope", expanded=False):
            category_data = melted_data[melted_data["Category"] == category]

            chart = (
                alt.Chart(category_data)
                .mark_bar(size=40)
                .encode(
                    x=alt.X("Type:N", title="Type", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Amount:Q", title="Amount (RM)"),
                    color=alt.Color(
                        "Type:N",
                        scale=alt.Scale(
                            domain=value_cols,
                            range=["#90caf9", "#1565c0", "#81c784"][: len(value_cols)],
                        ),
                    ),
                    tooltip=["Category", "Type", "Amount:Q"],
                )
                .properties(
                    title=f"Estimated vs Actual vs Envelope for {category}",
                    width=180,
                    height=250,
                )
                .configure_view(continuousWidth=350, continuousHeight=250)
                .configure_mark(opacity=0.9)
            )

            st.altair_chart(chart, use_container_width=True)

            st.markdown(f"### 🔍 Insights for {category}")
            st.markdown(
                f"""
            - **Category Overview**: This chart compares your estimated, actual, and envelope values for **{category}**.
            - **Key Insight**: If the 'Actual' bar exceeds the 'Estimated' bar, you're overspending in this category.
            - **Actionable Advice**: Consider tightening non-essential expenses or increasing your estimated envelope to match reality.
            """,
                unsafe_allow_html=True,
            )


def _spending_pie_chart(df: pd.DataFrame):
    st.markdown("### 🥧 Spending Breakdown by Category (Actual)")

    if df.empty or "Category" not in df.columns or "Actual (RM)" not in df.columns:
        st.info("Not enough data to show the spending breakdown yet.")
        return

    pie_df = (
        df.groupby("Category", as_index=False)["Actual (RM)"]
        .sum()
        .rename(columns={"Actual (RM)": "Actual"})
    )
    pie_df = pie_df[pie_df["Actual"] > 0]

    if pie_df.empty:
        st.info("No recorded spending yet.")
        return

    chart = (
        alt.Chart(pie_df)
        .mark_arc()
        .encode(
            theta="Actual:Q",
            color="Category:N",
            tooltip=["Category", alt.Tooltip("Actual:Q", format=",.2f")],
        )
        .properties(height=350)
    )

    st.altair_chart(chart, use_container_width=True)

    st.markdown("### 🔍 Insights for Spending Breakdown")
    st.markdown(
        """
    - **Category Overview**: This pie chart shows your spending breakdown by category.
    - **Key Insight**: Large slices highlight your biggest spending areas.
    - **Actionable Advice**: If a non-essential category dominates the chart, consider trimming that area next cycle.
    """,
        unsafe_allow_html=True,
    )


def _spending_trend_chart(tx_df: pd.DataFrame):
    st.markdown("### 📊 Spending Trend Over Time")

    if tx_df.empty or "amount" not in tx_df.columns or "date" not in tx_df.columns:
        st.info("No transaction data available for spending trend.")
        return

    tx_df["date"] = pd.to_datetime(tx_df["date"], errors="coerce")
    daily_data = (
        tx_df.groupby(tx_df["date"].dt.date)["amount"]
        .sum()
        .reset_index()
        .rename(columns={"date": "Date", "amount": "Total Spending (RM)"})
    )

    if daily_data.empty:
        st.info("No valid transactions to plot overall spending trend.")
        return

    overall_chart = (
        alt.Chart(daily_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Total Spending (RM):Q", title="Total Spending (RM)"),
            tooltip=["Date", alt.Tooltip("Total Spending (RM):Q", format=",.2f")],
        )
        .properties(height=280)
    )

    st.altair_chart(overall_chart, use_container_width=True)

    st.markdown("### 🔍 Insights for Spending Trend")
    st.markdown(
        """
    - **Trend Overview**: This chart tracks how your spending moves day by day.
    - **Key Insight**: A rising pattern suggests increased spending or one-off big payments.
    - **Actionable Advice**: Investigate spikes, link them to categories, and decide if they are one-off or recurring.
    """,
        unsafe_allow_html=True,
    )


# ============================================================
#   OVERSPENDING TABLE + INSIGHTS
# ============================================================
def _overspending_table(df: pd.DataFrame):
    st.markdown("### 🚨 Overspending Items")

    if df.empty or "Estimated (RM)" not in df.columns or "Actual (RM)" not in df.columns:
        st.info("No overspending information available yet.")
        return

    over_df = df[df["Actual (RM)"] > df["Estimated (RM)"]].copy()
    if over_df.empty:
        st.success("Nice work. You have no overspending items at the moment.")
        return

    over_df["Difference (RM)"] = over_df["Actual (RM)"] - over_df["Estimated (RM)"]

    def style_row(row):
        return [
            "background-color:#ffebee; color:#b71c1c; font-weight:600;"
            if row["Actual (RM)"] > row["Estimated (RM)"]
            else ""
        ] * len(row)

    display_df = over_df[
        ["Category", "Item", "Estimated (RM)", "Actual (RM)", "Difference (RM)", "Status"]
    ].copy()

    for c in ["Estimated (RM)", "Actual (RM)", "Difference (RM)"]:
        display_df[c] = display_df[c].map(lambda x: f"{x:,.2f}")

    styled = display_df.style.apply(style_row, axis=1)
    st.markdown(
        "<div class='scroll-table'>" + styled.to_html(index=False) + "</div>",
        unsafe_allow_html=True,
    )


def _smart_insights(df: pd.DataFrame, income: float):
    st.markdown("### 🧠 SmartSpend Insights")

    if df.empty or "Estimated (RM)" not in df.columns or "Actual (RM)" not in df.columns:
        st.info("Insights will appear here once you have some budget and transaction data.")
        return

    total_est = float(df["Estimated (RM)"].sum())
    total_act = float(df["Actual (RM)"].sum())

    exceeded_items = df[df["Actual (RM)"] > df["Estimated (RM)"]]
    underspent_items = df[(df["Actual (RM)"] > 0) & (df["Actual (RM)"] < df["Estimated (RM)"])]

    messages = []

    if total_act == 0:
        messages.append(
            "You have set up your budget but have not started recording actual spending yet."
        )
    else:
        utilisation = (total_act / income * 100) if income > 0 else 0
        if utilisation < 50:
            messages.append(
                f"Your total spending is around {utilisation:.1f}% of your income. "
                f"You still have healthy room to save or reallocate."
            )
        elif utilisation <= 90:
            messages.append(
                f"Your total spending is around {utilisation:.1f}% of your income. "
                f"Spending is within a reasonable range. Keep tracking closely."
            )
        else:
            messages.append(
                f"Your total spending is around {utilisation:.1f}% of your income. "
                f"You are very close to your income limit. Consider tightening a few categories."
            )

    if not exceeded_items.empty:
        top_over = (
            exceeded_items.assign(Diff=lambda d: d["Actual (RM)"] - d["Estimated (RM)"])
            .groupby("Category")["Diff"]
            .sum()
            .sort_values(ascending=False)
        )
        worst_cat = top_over.index[0]
        worst_val = top_over.iloc[0]
        messages.append(
            f"You are overspending the most in **{worst_cat}** "
            f"by approximately {_format_rm(worst_val)}."
        )

    if not underspent_items.empty:
        top_under = (
            underspent_items.assign(Diff=lambda d: d["Estimated (RM)"] - d["Actual (RM)"])
            .groupby("Category")["Diff"]
            .sum()
            .sort_values(ascending=False)
        )
        best_cat = top_under.index[0]
        best_val = top_under.iloc[0]
        messages.append(
            f"You are spending less than planned in **{best_cat}** "
            f"by about {_format_rm(best_val)}. You may reallocate or save this amount."
        )

    if "Envelope (RM)" in df.columns:
        low_env = df[df["Envelope (RM)"] < (0.2 * df["Estimated (RM)"])]
        low_env = low_env[low_env["Envelope (RM)"] > 0]
        if not low_env.empty:
            item_names = ", ".join(low_env["Item"].head(3).tolist())
            messages.append(
                f"Some envelopes are almost depleted compared to their estimated amounts. "
                f"Watch items like: {item_names}."
            )

    if "Status" in df.columns:
        status_counts = df["Status"].value_counts()
        if "Completed" in status_counts or "Pending" in status_counts:
            messages.append(
                f"You have {int(status_counts.get('Completed', 0))} completed items "
                f"and {int(status_counts.get('Pending', 0))} still pending."
            )

    html = "<div class='insight-card'><ul>"
    for msg in messages:
        html += f"<li>✅ {msg}</li>"
    html += "</ul></div>"

    st.markdown(html, unsafe_allow_html=True)


# ============================================================
#   MONTH-TO-MONTH COMPARISON
# ============================================================
def _month_comparison(tx_df: pd.DataFrame):
    st.markdown("### 📅 Month to Month Spending Comparison")

    if tx_df.empty or "amount" not in tx_df.columns or "date" not in tx_df.columns:
        st.info(
            "Month comparison will be available once you have at least one month of transaction data."
        )
        return

    tx_df = tx_df.dropna(subset=["date"])
    tx_df["month"] = tx_df["date"].dt.to_period("M").dt.to_timestamp()

    month_sum = (
        tx_df.groupby("month")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "Total"})
    )

    if month_sum.shape[0] < 2:
        st.info("Need at least two months of transactions to compare trends.")
        return

    month_sum["Change (RM)"] = month_sum["Total"].diff()
    month_sum["Change (%)"] = month_sum["Total"].pct_change() * 100

    chart = (
        alt.Chart(month_sum)
        .mark_bar()
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("Total:Q", title="Total Spending (RM)"),
            tooltip=[
                "month",
                alt.Tooltip("Total:Q", format=",.2f"),
                alt.Tooltip("Change (RM):Q", format=",.2f"),
                alt.Tooltip("Change (%):Q", format=".1f"),
            ],
        )
        .properties(height=280)
    )
    st.altair_chart(chart, use_container_width=True)

    display = month_sum.copy()
    display["Total"] = display["Total"].map(lambda x: f"{x:,.2f}")
    display["Change (RM)"] = display["Change (RM)"].map(
        lambda x: f"{x:,.2f}" if pd.notnull(x) else "-"
    )
    display["Change (%)"] = display["Change (%)"].map(
        lambda x: f"{x:.1f}%" if pd.notnull(x) else "-"
    )
    st.dataframe(display.rename(columns={"month": "Month"}), use_container_width=True)

    st.markdown("### 🔍 Insights for Month-to-Month Comparison")
    st.markdown(
        """
    - **Trend**: Bars show how your monthly total spending is changing.
    - **Key Insight**: Sudden jumps may indicate lifestyle changes or big events.
    - **Actionable Advice**: Use this view before adjusting next month’s budget limits.
    """,
        unsafe_allow_html=True,
    )


def _financial_health_kpis(df: pd.DataFrame, tx_df: pd.DataFrame, income: float):
    if df.empty or income <= 0:
        st.info("Financial Health Score will appear once you have a budget and income set.")
        return

    total_est = float(df["Estimated (RM)"].sum()) if "Estimated (RM)" in df.columns else 0.0
    total_act = float(df["Actual (RM)"].sum()) if "Actual (RM)" in df.columns else 0.0
    total_env = float(df["Envelope (RM)"].sum()) if "Envelope (RM)" in df.columns else 0.0

    savings = max(income - total_act, 0.0)
    savings_rate = savings / income
    overspend_amount = float(
        (df.get("Actual (RM)", 0) - df.get("Estimated (RM)", 0)).clip(lower=0).sum()
    )
    denom = (total_est + 1e-6)
    overspend_ratio = overspend_amount / denom
    envelope_ratio = total_env / denom

    raw_score = 50 + 30 * savings_rate - 30 * overspend_ratio + 20 * envelope_ratio
    health_score = max(0, min(100, raw_score))

    if health_score >= 80:
        band = "Excellent"
        css_class = "kpi-good"
    elif health_score >= 60:
        band = "Healthy"
        css_class = "kpi-good"
    elif health_score >= 40:
        band = "Caution"
        css_class = "kpi-medium"
    else:
        band = "At Risk"
        css_class = "kpi-bad"

    utilisation = (total_act / income) * 100 if income > 0 else 0
    if utilisation < 60 and overspend_ratio < 0.05:
        risk_label = "Low Risk"
        risk_desc = "Spending is generally within safe limits. Keep it up."
        risk_class = "kpi-good"
    elif utilisation <= 90 and overspend_ratio < 0.15:
        risk_label = "Moderate Risk"
        risk_desc = "Tracking is okay, but watch a few categories."
        risk_class = "kpi-medium"
    else:
        risk_label = "High Risk"
        risk_desc = "You are close to or above your comfort zone. Rebalance soon."
        risk_class = "kpi-bad"

    savings_pct = savings_rate * 100

    st.markdown("### 🤖 SmartSpend Intelligence Layer")
    st.caption("Automated health check on your overall budget and risk profile.")

    st.markdown(
        f"""
        <div class="kpi-strip">
            <div class="kpi-card {css_class}">
                <div class="kpi-title">Financial Health Score</div>
                <div class="kpi-value">{health_score:.0f}/100</div>
                <div class="kpi-sub">Status: <b>{band}</b></div>
            </div>
            <div class="kpi-card {risk_class}">
                <div class="kpi-title">SmartSpend AI Risk Meter</div>
                <div class="kpi-value">{risk_label}</div>
                <div class="kpi-sub">{risk_desc}</div>
            </div>
            <div class="kpi-card kpi-good">
                <div class="kpi-title">Savings Rate (This Cycle)</div>
                <div class="kpi-value">{savings_pct:.1f}%</div>
                <div class="kpi-sub">Approx. savings: RM {savings:,.2f}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _savings_projection_forecast(df: pd.DataFrame, tx_df: pd.DataFrame, income: float):
    st.markdown("### 💡 Savings Projection Forecast (Next 6 Months)")

    if income <= 0:
        st.info("Please set your income to activate savings projection.")
        return

    if tx_df.empty or "date" not in tx_df.columns or "amount" not in tx_df.columns:
        st.info("Savings projection will appear once you have recorded dated expenses.")
        return

    tx = tx_df.copy()
    tx["date"] = pd.to_datetime(tx["date"], errors="coerce")
    tx = tx.dropna(subset=["date", "amount"])

    if "type" in tx.columns:
        tx = tx[~tx["type"].str.contains("top up|transfer", case=False, na=False)]

    if tx.empty:
        st.info("Only top-ups/transfers detected. No real expenses for projection.")
        return

    tx["month"] = tx["date"].dt.to_period("M").dt.to_timestamp()
    monthly = tx.groupby("month")["amount"].sum().reset_index().sort_values("month")

    if monthly.empty:
        st.info("No valid transactions for projection.")
        return

    q1 = monthly["amount"].quantile(0.25)
    q3 = monthly["amount"].quantile(0.75)
    iqr = q3 - q1
    upper_limit = q3 + 1.5 * iqr
    monthly["clean_amount"] = monthly["amount"].clip(upper=upper_limit)

    monthly["Savings"] = income - monthly["clean_amount"]
    monthly["Savings"] = monthly["Savings"].clip(lower=-income)

    base_savings = monthly["Savings"].median()
    monthly["idx"] = range(1, len(monthly) + 1)
    a, b = np.polyfit(monthly["idx"], monthly["Savings"], 1)

    trend_factor = max(-0.20, min(0.20, a / (abs(base_savings) + 1e-6)))

    last_month = monthly["month"].max()
    future_months = pd.date_range(
        start=last_month + pd.offsets.MonthBegin(1),
        periods=6,
        freq="MS",
    )

    projected_values = []
    current = base_savings
    for _ in range(6):
        current = current * (1 + trend_factor)
        current = max(-income, min(income, current))
        projected_values.append(current)

    proj_df = pd.DataFrame(
        {"month": future_months, "Savings": projected_values, "Type": "Projected"}
    )

    hist_df = monthly[["month", "Savings"]].copy()
    hist_df["Type"] = "Historical"
    combined = pd.concat([hist_df, proj_df], ignore_index=True)

    chart = (
        alt.Chart(combined)
        .mark_line(point=True)
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("Savings:Q", title="Savings (RM)"),
            color=alt.Color(
                "Type:N",
                scale=alt.Scale(
                    domain=["Historical", "Projected"], range=["#1565c0", "#43a047"]
                ),
            ),
            tooltip=[
                alt.Tooltip("month:T", title="Month"),
                alt.Tooltip("Savings:Q", title="Savings (RM)", format=",.2f"),
                "Type",
            ],
        )
        .properties(height=300)
    )

    st.altair_chart(chart, use_container_width=True)

    avg_hist = monthly["Savings"].mean()
    st.caption(
        f"Projection is based on your median historical savings and a capped trend factor. "
        f"Your average historical savings: RM {avg_hist:,.2f}."
    )


def _next_month_spending_prediction(tx_df: pd.DataFrame, income: float):
    st.markdown("### 🔮 Next Month Spending Prediction")

    if tx_df.empty or "date" not in tx_df.columns or "amount" not in tx_df.columns:
        st.info("Prediction will appear once you have at least one month of spending data.")
        return

    if income <= 0:
        st.info("Please set your income for realistic prediction.")
        return

    tx = tx_df.copy()
    tx["date"] = pd.to_datetime(tx["date"], errors="coerce")
    tx = tx.dropna(subset=["date", "amount"])

    if "type" in tx.columns:
        tx = tx[~tx["type"].str.contains("top up|transfer", case=False, na=False)].copy()

    if tx.empty:
        st.info("Only top-ups/transfers detected. No real spending data yet.")
        return

    tx["month"] = tx["date"].dt.to_period("M").dt.to_timestamp()
    monthly = tx.groupby("month")["amount"].sum().reset_index().sort_values("month")

    if monthly.empty:
        st.info("Need transactions with valid dates.")
        return

    q1 = monthly["amount"].quantile(0.25)
    q3 = monthly["amount"].quantile(0.75)
    iqr = q3 - q1
    upper_limit = q3 + 1.5 * iqr
    monthly["clean_amount"] = monthly["amount"].clip(upper=upper_limit)

    if monthly.shape[0] == 1:
        predicted = float(monthly["clean_amount"].iloc[0])
        current_spend = predicted
    else:
        base_value = monthly["clean_amount"].median()
        monthly["idx"] = range(1, len(monthly) + 1)
        a, b = np.polyfit(monthly["idx"], monthly["clean_amount"], 1)
        trend_adjustment = max(-0.15, min(0.15, a / (base_value + 1e-6)))
        predicted = base_value * (1 + trend_adjustment)
        current_spend = float(monthly["clean_amount"].iloc[-1])

    predicted = max(0, predicted)
    predicted = min(predicted, income * 1.10)

    utilisation_pred = (predicted / income) * 100

    if utilisation_pred < 60:
        label = "Comfortable"
        color = "#4caf50"
    elif utilisation_pred <= 90:
        label = "Tight but manageable"
        color = "#ff9800"
    else:
        label = "Potentially overstretched"
        color = "#f44336"

    st.markdown(
        f"""
        <div class="kpi-strip">
            <div class="kpi-card">
                <div class="kpi-title">Predicted Spending Next Month</div>
                <div class="kpi-value">RM {predicted:,.2f}</div>
                <div class="kpi-sub">Smoothed prediction based on past transactions.</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Last Recorded Month</div>
                <div class="kpi-value">RM {current_spend:,.2f}</div>
                <div class="kpi-sub">After outlier filtering.</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Prediction Assessment</div>
                <div class="kpi-value" style="color:{color};">{label}</div>
                <div class="kpi-sub">Estimated utilisation of income: {utilisation_pred:.1f}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _dti_radar_chart(tx_df: pd.DataFrame, income: float):
    st.markdown("### 🧭 Debt-to-Income Radar Chart")

    if income <= 0:
        st.info("Set your income before calculating debt-to-income ratios.")
        return

    if tx_df.empty or "category" not in tx_df.columns or "amount" not in tx_df.columns:
        st.info(
            "Debt-related spending will be shown once you record transactions with categories."
        )
        return

    df = tx_df.copy()
    df["category"] = df["category"].fillna("").str.lower()

    housing_mask = df["category"].str.contains("rent|mortgage|housing|home loan")
    car_mask = df["category"].str.contains("car|auto|vehicle|hp")
    personal_mask = df["category"].str.contains("loan|debt|credit|ptptn|hire purchase")

    housing_debt = float(df.loc[housing_mask, "amount"].sum())
    car_debt = float(df.loc[car_mask, "amount"].sum())
    personal_debt = float(df.loc[personal_mask, "amount"].sum())

    housing_pct = min(100.0, (housing_debt / income) * 100)
    car_pct = min(100.0, (car_debt / income) * 100)
    personal_pct = min(100.0, (personal_debt / income) * 100)

    if housing_pct == 0 and car_pct == 0 and personal_pct == 0:
        st.info(
            "No debt-like categories (loans, credit cards, etc.) detected in your transactions yet."
        )
        return

    labels = ["Housing Debt", "Car / Transport Debt", "Personal / Other Debt"]
    stats = [housing_pct, car_pct, personal_pct]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    stats_cycle = stats + [stats[0]]
    angles_cycle = np.concatenate([angles, [angles[0]]])

    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles_cycle, stats_cycle, linewidth=2)
    ax.fill(angles_cycle, stats_cycle, alpha=0.25)

    ax.set_thetagrids(angles * 180 / np.pi, labels)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"])
    ax.set_title("Debt Components as % of Income", fontsize=12, pad=16)

    st.pyplot(fig)

    st.caption(
        "This chart approximates debt-related payments by scanning your categories for terms such as "
        "rent, mortgage, loan, credit card, and hire purchase."
    )

    st.markdown("### 🔍 Insights for Debt-to-Income Chart")
    st.markdown(
        """
    - **Debt-to-Income Ratio**: Shows how much of your income is going into housing, car, and personal debt.
    - **Key Insight**: If any debt slice is too large, it may be squeezing your savings.
    - **Actionable Advice**: Consider refinancing, restructuring, or paying down high-interest debt first.
    """,
        unsafe_allow_html=True,
    )


def create_chart_from_budget(df_budget: pd.DataFrame):
    if df_budget.empty or "Category" not in df_budget.columns:
        raise ValueError("No budget data available to plot.")

    for col in ["Estimated (RM)", "Actual (RM)"]:
        if col not in df_budget.columns:
            raise ValueError(f"Missing required column: {col}")

    budget_summary = (
        df_budget.groupby("Category")
        .agg({"Estimated (RM)": "sum", "Actual (RM)": "sum"})
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(
        budget_summary["Category"],
        budget_summary["Estimated (RM)"],
        label="Estimated",
        alpha=0.7,
        color="skyblue",
    )
    ax.bar(
        budget_summary["Category"],
        budget_summary["Actual (RM)"],
        label="Actual",
        alpha=0.7,
        color="orange",
    )

    ax.set_xlabel("Categories")
    ax.set_ylabel("Amount (RM)")
    ax.set_title("Budget vs Actual by Category")
    ax.legend()
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    save_path = "./charts/"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    chart_path = os.path.join(save_path, "chart.png")
    plt.savefig(chart_path)
    plt.close()

    return chart_path


def generate_analysis_pdf(
    df_budget: pd.DataFrame,
    df_transactions: pd.DataFrame,
    analysis_title: str,
    analysis_details: str,
    income: float,
):
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        if os.path.exists(LOGO_PATH):
            logo = RLImage(LOGO_PATH, width=100, height=50)
            elements.append(logo)
            elements.append(Spacer(1, 12))

        title = Paragraph(f"<b>{analysis_title}</b>", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 12))

        details = Paragraph(analysis_details, styles["Normal"])
        elements.append(details)
        elements.append(Spacer(1, 12))

        total_est = df_budget["Estimated (RM)"].sum() if "Estimated (RM)" in df_budget.columns else 0.0
        total_act = df_budget["Actual (RM)"].sum() if "Actual (RM)" in df_budget.columns else 0.0
        total_env = df_budget["Envelope (RM)"].sum() if "Envelope (RM)" in df_budget.columns else 0.0
        diff = total_est - total_act
        remaining_income = income - total_act

        summary = f"""
        <b>Summary of Budget:</b><br/>
        - Total Estimated: RM {total_est:,.2f}<br/>
        - Total Actual: RM {total_act:,.2f}<br/>
        - Envelope Balance: RM {total_env:,.2f}<br/>
        - Difference (Estimated - Actual): RM {diff:,.2f}<br/>
        - Remaining Income: RM {remaining_income:,.2f}<br/>
        """
        summary_paragraph = Paragraph(summary, styles["Normal"])
        elements.append(summary_paragraph)
        elements.append(Spacer(1, 12))

        # Chart is optional – if it fails, we still build the PDF
        try:
            chart_image_path = create_chart_from_budget(df_budget)
            if os.path.exists(chart_image_path):
                chart_image = RLImage(chart_image_path, width=400, height=300)
                elements.append(chart_image)
                elements.append(Spacer(1, 12))
        except Exception as e:
            # Soft fail: just warn in the app, no crash
            st.warning(f"Chart could not be generated for PDF: {e}")

        # Budget table
        if not df_budget.empty and all(
            col in df_budget.columns
            for col in ["Category", "Item", "Estimated (RM)", "Actual (RM)", "Status"]
        ):
            data = [["Category", "Item", "Estimated (RM)", "Actual (RM)", "Status"]]
            for _, row in df_budget.iterrows():
                data.append(
                    [
                        row["Category"],
                        row["Item"],
                        f"{row['Estimated (RM)']:.2f}",
                        f"{row['Actual (RM)']:.2f}",
                        row["Status"],
                    ]
                )

            table = Table(data, colWidths=[100, 150, 100, 100, 100])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                    ]
                )
            )
            elements.append(table)

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()

        return pdf_data

    except Exception as e:
        st.warning(f"⚠️ Could not generate the analysis PDF: {e}")
        return None


# ============================================================
#   MAIN
# ============================================================
def analysis_page():
    ensure_analytics_schema()
    apply_bg()

    if "user_id" not in st.session_state:
        st.error("User ID not found. Please log in again.")
        st.stop()

    user_id = st.session_state.user_id

    st.markdown(
        "<h1 style='color:#003366; text-align:center;'>📊 SmartSpend Analytics</h1>",
        unsafe_allow_html=True,
    )

    df_budget = load_budget_df(user_id)
    tx_df = load_transactions_df(user_id)
    income = float(get_income(user_id) or 0.0)

    _summary_cards(df_budget, income)

    analysis_title = "SmartSpend Budget Analysis Report"
    analysis_details = """
            This report provides an overview of your planned vs actual expenses for the month. It includes the 
            budgeted amounts, actual expenses, and the current status of each category.
            """

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Generate Analysis PDF Report"):
        pdf_data = generate_analysis_pdf(df_budget, tx_df, analysis_title, analysis_details, income)

        if pdf_data:
            st.download_button(
                label="Download Analysis Report",
                data=pdf_data,
                file_name="analysis_report.pdf",
                mime="application/pdf",
            )

    st.markdown("<hr style='border: 0.5px solid #181601; margin: 30px 0;'>", unsafe_allow_html=True)

    st.markdown(
        "<h2 style='color:#003366; text-align:left;'>🧠SmartSpend Advanced Intelligence Layer</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Automated projection, wellness scoring, and debt evaluation.")

    with st.expander("📊 Financial Health KPIs", expanded=False):
        _financial_health_kpis(df_budget, tx_df, income)
    with st.expander("💡 Savings Projection Forecast", expanded=False):
        _savings_projection_forecast(df_budget, tx_df, income)
    with st.expander("🔮 Next Month Spending Prediction", expanded=False):
        _next_month_spending_prediction(tx_df, income)
    with st.expander("🧭 Debt-to-Income Radar Chart", expanded=False):
        _dti_radar_chart(tx_df, income)

    st.markdown("<hr style='border: 0.5px solid #181601; margin: 30px 0;'>", unsafe_allow_html=True)

    st.markdown(
        "<h2 style='color:#003366; text-align:center;'>📉Visual Analytics</h2>",
        unsafe_allow_html=True,
    )

    with st.expander("📊 Category Budget vs Actual vs Envelope Allocation", expanded=False):
        _category_comparison_chart(df_budget)

    with st.expander("🥧 Spending Breakdown by Category", expanded=False):
        _spending_pie_chart(df_budget)

    with st.expander("📈 Time Based Trends", expanded=False):
        _spending_trend_chart(tx_df)
        _month_comparison(tx_df)

    with st.expander("🚨 Overspending & Insights", expanded=False):
        _overspending_table(df_budget)
        _smart_insights(df_budget, income)

    st.markdown("<hr style='border: 0.5px solid #181601; margin: 30px 0;'>", unsafe_allow_html=True)

    nav1, nav2, nav3 = st.columns(3)
    with nav1:
        if st.button("🏠 Return to Main Menu", use_container_width=True):
            st.session_state.page = "main_menu"
            st.rerun()
    with nav2:
        if st.button("🎯 Go to MoneyMagic", use_container_width=True):
            st.session_state.page = "money_magic"
            st.rerun()
    with nav3:
        if st.button("🗺️ Go to Money Map", use_container_width=True):
            st.session_state.page = "money_map"
            st.rerun()

    st.markdown("<hr style='border: 0.5px solid #181601; margin: 30px 0;'>", unsafe_allow_html=True)

    st.markdown("##### 🤑 WANT MORE ADVISE ? No FEAR for MONEYTALKS is HERE 😎")

    image_path = r"C:\Users\sharv\Downloads\UOW\FYP\FYP2\moneytalks_advisor.png"
    if os.path.exists(image_path):
        st.image(image_path, width=150)

    if st.button("HI FRIEND ! I am Money Talks ! Need My Help ?", key="moneytalks_redirect"):
        st.session_state.page = "moneytalks"
        st.rerun()

    st.markdown(
        """
        <div class='footer-note'>
            <span style='color:#003366; font-size:20px;'>
                SmartSpend - The Intelligence of Finance
            </span><br>
            <span style='color:#00008B; font-size:20px; font-weight:600;'>
                SmartSpend 2025. FYP by Sharvena A/P Kumaran
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
