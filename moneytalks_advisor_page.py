#Author : Sharvena A/P Kumaran
#Student ID : 0128131
#FYP PROJECT 2025 UNIVERSITY OF WOLLONGONG MALAYSIA
# moneytalks_advisor_page.py
import os
import base64
import sqlite3
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, Tuple
import streamlit as st

# ============================================================
#   BACKGROUND & THEME
# ============================================================
BG_PATH = r"C:/Users/sharv/Downloads/UOW/FYP/FYP2/AI advisor bg.jpg"

def _encode_local_image_to_base64(path: str) -> str | None:
    try:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    return None

def apply_bg_and_theme():
    b64 = _encode_local_image_to_base64(BG_PATH)
    bg_css = ""
    if b64:
        bg_css = f"""
            .stApp {{
                background: url("data:image/jpeg;base64,{b64}") no-repeat center center fixed;
                background-size: cover;
            }}
            .blur-overlay {{
                position: fixed; inset: 0;
                backdrop-filter: blur(6px) brightness(0.93);
                z-index: -1;
            }}
        """
    st.markdown(
        f"""
        <style>
            {bg_css}
            .card {{
                background: rgba(255,255,255,0.96);
                color: #003366;
                font-weight: 600;
                padding: 18px;
                border-radius: 12px;
                margin: 8px 0;
                box-shadow: 0 4px 10px rgba(0,0,0,0.12);
            }}
            div.stButton>button {{
                background: linear-gradient(to right,#ffffba,#baffc9,#bae1ff);
                color:#003366; border:none; border-radius:8px;
                padding:0.6em 1.5em; font-weight: 800 !important; letter-spacing: 0.3px; font-size:16px;
                cursor:pointer; transition:0.25s ease;
            }}
            div.stButton>button:hover {{ filter:brightness(1.05); transform:scale(1.02); }}
        </style>
        <div class="blur-overlay"></div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar colour styling
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #E9BBFC;
    }
    [data-testid="stSidebar"] * {
        color: #003366 !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
#   DB HELPERS — REUSE EXISTING FILES
# ============================================================
DB_PATH = "smartspend.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def safe_sum(x):
    try:
        return float(x) if x is not None else 0.0
    except Exception:
        return 0.0

# Import ONLY the functions that exist
from money_magic_page_file import get_income


# ============================================================
#   FETCH USER-SPECIFIC BUDGET
# ============================================================
def fetch_budget_df(user_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Ensure required columns exist
        cur.execute("PRAGMA table_info(money_magic_budget);")
        cols = [r[1] for r in cur.fetchall()]

        if "created_at" not in cols:
            cur.execute("ALTER TABLE money_magic_budget ADD COLUMN created_at TEXT;")

        if "updated_at" not in cols:
            cur.execute("ALTER TABLE money_magic_budget ADD COLUMN updated_at TEXT;")

        if "user_id" not in cols:
            cur.execute("ALTER TABLE money_magic_budget ADD COLUMN user_id INTEGER;")

        conn.commit()

        df = pd.read_sql_query("""
            SELECT
                category AS Category,
                item_name AS Item,
                estimated_amount AS 'Estimated (RM)',
                actual_amount AS 'Actual (RM)',
                status AS Status,
                created_at AS Created,
                COALESCE(updated_at, created_at) AS 'Last Updated'
            FROM money_magic_budget
            WHERE user_id = ?
            ORDER BY category, item_name;
        """, conn, params=(user_id,))
    finally:
        conn.close()

    return df


def fetch_income(user_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT monthly_income
        FROM money_magic_income
        WHERE user_id = ?
        LIMIT 1;
    """, (user_id,))

    row = cur.fetchone()
    conn.close()

    return float(row[0]) if row and row[0] is not None else 0.0

# ============================================================
#   BUDGET TOTALS & PERIODS
# ============================================================
def totals_and_remaining(df: pd.DataFrame, income: float) -> Tuple[float, float, float]:
    est = safe_sum(df["Estimated (RM)"].sum()) if not df.empty else 0.0
    act = safe_sum(df["Actual (RM)"].sum()) if not df.empty else 0.0
    remaining = float(income) - float(act)
    return est, act, remaining

def budget_period_from_session():
    start = st.session_state.get("budget_start")
    end = st.session_state.get("budget_end")
    if isinstance(start, pd.Timestamp): start = start.date()
    if isinstance(end, pd.Timestamp): end = end.date()
    return start, end

def days_left(end: date | None):
    return (end - date.today()).days if end else None


# ============================================================
#   LOCAL SPENDING DECISION ENGINE
# ============================================================
def local_affordability_check(price_rm: float, remaining: float, end: date | None):
    if price_rm <= 0:
        return {"decision": "APPROVE", "explain": "Amount is zero or negative."}

    days = days_left(end)
    cushion_ratio = 0.25
    min_cushion = remaining * cushion_ratio if remaining > 0 else 0.0

    if remaining - price_rm < 0:
        return {
            "decision": "RECONSIDER",
            "explain": f"This would put you RM {abs(remaining - price_rm):,.2f} below zero."
        }

    if days and days <= 3:
        min_cushion = remaining * 0.35

    if (remaining - price_rm) < min_cushion:
        return {
            "decision": "CAUTION",
            "explain": f"It leaves a thin buffer (below cushion RM {min_cushion:,.2f})."
        }

    return {"decision": "APPROVE", "explain": "Purchase fits within the buffer."}


# ============================================================
#   LOCAL LLM (OLLAMA CALL)
# ============================================================
import requests
import json

def call_moneytalks_llm_local(context, user_text):
    try:
        prompt = f"""
        You are MoneyTalks, a Malaysian AI advisor inside SmartSpend.
        Use Ringgit (RM).
        Context: {json.dumps(context, ensure_ascii=False, indent=2)}
        User: {user_text}
        """

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "gemma3:1b", "prompt": prompt},
            stream=True,
            timeout=120
        )

        full_text = ""
        for line in response.iter_lines(decode_unicode=True):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if "response" in data:
                    full_text += data["response"]
            except json.JSONDecodeError:
                continue

        return full_text.strip() or "⚠️ No response received."
    except Exception as e:
        return f"⚠️ Error: {e}"


# ============================================================
#   MAIN PAGE
# ============================================================
# moneytalks_advisor_page.py

# Other imports and code remain the same...

def moneytalks_page():
    apply_bg_and_theme()

    # User ID guard — ensure session is user-specific
    user_id = st.session_state.get("user_id")
    if user_id is None:
        st.error("You must log in to use MoneyTalks.")
        return

    # --- Header Image ---
    image_path = r"C:\Users\sharv\Downloads\UOW\FYP\FYP2\moneytalks_advisor.png"
    st.markdown(
        f'<div style="text-align: center;"><img src="data:image/png;base64,{base64.b64encode(open(image_path, "rb").read()).decode()}" width="300"></div>',
        unsafe_allow_html=True
    )
    st.markdown("<h1 style='text-align:center;color:#003366;'>MoneyTalks</h1>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;color:#003366;'>Your Personal AI Financial Advisor</h1>", unsafe_allow_html=True)

    # --- Load Data ---
    income = fetch_income(user_id)
    df = fetch_budget_df(user_id)
    est, act, remaining = totals_and_remaining(df, income)
    start, end = budget_period_from_session()
    daysleft = days_left(end)

    # --- Budget Velocity ---
    exceeded_items = []
    near_limit_items = []

    if not df.empty:
        for _, r in df.iterrows():
            est_i = safe_sum(r["Estimated (RM)"])
            act_i = safe_sum(r["Actual (RM)"])
            if est_i > 0:
                if act_i > est_i:
                    exceeded_items.append(f"{r['Item']} (+RM {act_i - est_i:,.2f})")
                elif act_i >= 0.9 * est_i:
                    near_limit_items.append(f"{r['Item']} ({act_i/est_i*100:.0f}%)")

    vel_msg = "On track"
    if est > 0:
        ratio = act / est
        if ratio > 1.1:
            vel_msg = "⚠️ Spending faster than planned."
        elif ratio > 0.9:
            vel_msg = "Close to limit."

    # --- Dashboard Card ---
    st.markdown(f"""
    <div class='card'>
        <b>Income:</b> RM {income:,.2f} |
        <b>Estimated:</b> RM {est:,.2f} |
        <b>Actual:</b> RM {act:,.2f} |
        <b>Remaining:</b> RM {remaining:,.2f}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================
    #   SIDEBAR CHECKS
    # ============================================================
    with st.sidebar:
        st.subheader("MoneyTalks Quick Check")
        amt = st.number_input("Planned purchase (RM)", min_value=0.0, step=50.0)
        note = st.text_input("What is it for? (optional)")

        if st.button("Run Affordability Check"):
            result = local_affordability_check(amt, remaining, end)
            st.info(f"{result['decision']} — {result['explain']}")

        if st.button("Clear Chat History"):
            st.session_state.pop(f"moneytalks_history_{user_id}", None)  # Ensure unique history for each user
            st.success("Chat cleared.")

    # ============================================================
    #   CHAT HISTORY
    # ============================================================
    if f"moneytalks_history_{user_id}" not in st.session_state:
        username = st.session_state.get("username", "there")
        st.session_state[f"moneytalks_history_{user_id}"] = [(
            "assistant",
            f"👋 Hi {username}, I’m <b>MoneyTalks</b> — your personalized financial advisor.<br><br>"
            "Any issues with finance? No fear, for <b>MoneyTalks</b> is here!😎<br><br>"
            "How may I assist you today my friend ?😊<br>"
        )]

    # --- Render History ---
    user_name = st.session_state.get("username", "You")

    for role, content in st.session_state[f"moneytalks_history_{user_id}"]:  # Use unique key for each user
        if role == "assistant":
            st.markdown(f"""
                <div style='background: rgba(234,187,252,0.96);
                            color:#003366; padding:15px; border-radius:12px;
                            margin:8px 0; box-shadow:0 4px 10px rgba(0,0,0,0.1);'>
                    {content}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style='background: linear-gradient(to right, #63CBF8, #BBE8FC);
                            color:#002244; padding:12px; border-radius:12px;
                            margin:8px 0 8px 40px; text-align:right;
                            box-shadow:0 4px 8px rgba(0,0,0,0.08);'>
                    <b>{user_name}:</b> {content}
                </div>
            """, unsafe_allow_html=True)

    # ============================================================
    #   CHAT INPUT BAR
    # ============================================================
    st.markdown("""
    <style>

    /* FORCE every layer of st.chat_input() to use pastel sky blue */
    div[data-testid="stChatInput"] * {
        background-color: #d8ecff !important;
        border-color: #aac5ff !important;
    }

    /* OUTER WRAPPER */
    div[data-testid="stChatInput"] {
        padding: 0 !important;
        border-radius: 40px !important;
    }

    /* INNER WRAPPER */
    div[data-testid="stChatInput"] > div {
        border: 2px solid #aac5ff !important;
        border-radius: 40px !important;
        padding: 6px 14px !important;
    }

    /* TEXTAREA (actual input box) */
    div[data-testid="stChatInput"] textarea {
    background-color: #d8ecff !important;
    color: #003366 !important;
    font-size: 20px !important;
    font-weight: 700 !important;

    height: 40px !important;            /* FIX CLIPPING */
    line-height: 40px !important;       /* CENTER TEXT */
    padding: 0 14px !important;         /* EVEN VERTICAL SPACE */

    border-radius: 40px !important;
    border: none !important;
    resize: none !important;
    }

    /* PLACEHOLDER */
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #6b7b8c !important;
        opacity: 0.7 !important;
    }

    /* SEND ARROW */
    div[data-testid="stChatInput"] svg {
        fill: #003366 !important;
        width: 28px !important;
        height: 28px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    user_text = st.chat_input("Ask MoneyTalks anything about your budget...")

    if user_text:
        st.session_state[f"moneytalks_history_{user_id}"].append(("user", user_text))  # Use unique key for each user

        ctx = {
            "period_str": f"{start} → {end}" if start and end else "Not set",
            "days_left": daysleft if daysleft is not None else "N/A",
            "income_rm": income,
            "est_rm": est,
            "act_rm": act,
            "remaining_rm": remaining,
            "velocity_msg": vel_msg,
            "exceeded_items": exceeded_items,
            "near_limit_items": near_limit_items,
        }

        reply = call_moneytalks_llm_local(ctx, user_text)

        st.session_state[f"moneytalks_history_{user_id}"].append(("assistant", reply))  # Use unique key for each user
        st.rerun()

    # ============================================================
    #   NAVIGATION
    # ============================================================
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🏠 Return to Main Menu", use_container_width=True):
        st.session_state.page = "main_menu"
        st.rerun()

    # ---------- FOOTER ----------
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
