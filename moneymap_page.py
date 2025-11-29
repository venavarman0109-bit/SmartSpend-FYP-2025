#Author : Sharvena A/P Kumaran
#Student ID : 0128131
#FYP PROJECT 2025 UNIVERSITY OF WOLLONGONG MALAYSIA
# moneymap_page.py

import os
import time
import base64
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta
from typing import Optional, Tuple

from login_register import send_email  # reuse your existing email helper
from money_magic_page_file import (
    get_conn,
    ensure_base_schema,
    get_income,
    get_current_user_id,
)

# ============================================================
#   BACKGROUND & STYLE
# ============================================================
BG_PATH = r"C:/Users/sharv/Downloads/UOW/FYP/FYP2/budget planner bg.jpg"


def _encode_local_image_to_base64(path: str) -> Optional[str]:
    try:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    return None


def apply_bg():
    b64 = _encode_local_image_to_base64(BG_PATH)
    if not b64:
        return
    st.markdown(
        f"""
        <style>
            .stApp {{
                background: url("data:image/jpeg;base64,{b64}") no-repeat center center fixed;
                background-size: cover;
            }}
            .blur-overlay {{
                position: fixed; inset: 0;
                backdrop-filter: blur(6px) brightness(0.93);
                z-index: -1;
            }}
            .scroll-table {{
                overflow-y: auto;
                max-height: 420px;
                background: rgba(254, 253, 231, 0.95);
                border-radius: 10px;
                padding: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }}
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
        </style>
        <div class="blur-overlay"></div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
#   DATABASE INITIALIZATION
# ============================================================
def init_schema():
    """
    Use base schema from MoneyMagic and then extend with:
    - smartspend_wallet (per-user wallet)
    - transactions (per-user transaction log)
    """
    ensure_base_schema()

    conn = get_conn()
    cur = conn.cursor()

    # Multi-user wallet table (per user)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS smartspend_wallet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            total_income REAL DEFAULT 0,
            total_budget REAL DEFAULT 0,
            spent REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            last_updated TEXT
        );
        """
    )

    # Transactions table (already includes user_id)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT,
            type TEXT,
            method TEXT,
            category TEXT,
            item TEXT,
            amount REAL,
            source TEXT,
            target TEXT,
            remarks TEXT
        );
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_tx_user_date ON transactions(user_id, date);"
    )

    conn.commit()
    conn.close()


def ensure_tracker_schema():
    conn = get_conn()
    cur = conn.cursor()
    # Add a tracker schema if it doesn't exist
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_tracker (
            user_id INTEGER PRIMARY KEY,
            tracker_active INTEGER DEFAULT 0,
            tracker_start_dt TEXT,
            tracker_end_dt TEXT
        );
        """
    )
    conn.commit()
    conn.close()


# ============================================================
#   DATA HELPERS (BUDGET)
# ============================================================
def fetch_budget_df() -> pd.DataFrame:
    conn = get_conn()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return pd.DataFrame()

    df = pd.read_sql_query(
        """
        SELECT
            category AS 'Category',
            item_name AS 'Item',
            estimated_amount AS 'Estimated (RM)',
            actual_amount AS 'Actual (RM)',
            envelope_balance AS 'Envelope (RM)',
            payment_progress AS 'Payment Progress',
            status AS 'Status'
        FROM money_magic_budget
        WHERE user_id = ?
        ORDER BY category, item_name;
        """,
        conn,
        params=(user_id,),
    )
    conn.close()
    return df


def fetch_line(category: str, item: str) -> Tuple[float, float, float]:
    """
    Fetch a single budget line (est, act, env) for the current user.
    """
    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return 0.0, 0.0, 0.0

    cur.execute(
        """
        SELECT estimated_amount, actual_amount, envelope_balance
        FROM money_magic_budget
        WHERE user_id = ? AND category = ? AND item_name = ?;
        """,
        (user_id, category, item),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return 0.0, 0.0, 0.0
    return float(row[0] or 0), float(row[1] or 0), float(row[2] or 0)


def set_status_and_progress(est, act):
    if act <= 0:
        return "Pending", "Not Paid"
    elif act < est:
        return "Active", "Partially Paid"
    elif act == est:
        return "Completed", "Fully Paid"
    else:
        return "Exceeded", "Over Budget"


def update_budget(category, item, delta_actual=0.0, delta_env=0.0):
    """
    Update actual and/or envelope for a specific line, scoped to current user.
    """
    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return

    est, act, env = fetch_line(category, item)
    act += float(delta_actual)
    env = max(0.0, env + float(delta_env))

    status, progress = set_status_and_progress(est, act)

    cur.execute(
        """
        UPDATE money_magic_budget
        SET actual_amount = ?,
            envelope_balance = ?,
            status = ?,
            payment_progress = ?,
            last_updated = ?
        WHERE user_id = ? AND category = ? AND item_name = ?;
        """,
        (
            act,
            env,
            status,
            progress,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_id,
            category,
            item,
        ),
    )
    conn.commit()
    conn.close()


# ============================================================
#   DATA HELPERS (WALLET + TRANSACTIONS)
# ============================================================
def get_income(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT monthly_income 
        FROM money_magic_income 
        WHERE user_id = ? 
        LIMIT 1;
        """,
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    return float(row[0]) if row and row[0] is not None else 0.0


def get_wallet_balance() -> float:
    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return 0.0

    cur.execute(
        "SELECT balance FROM smartspend_wallet WHERE user_id = ?;",
        (user_id,),
    )
    row = cur.fetchone()

    if not row:
        cur.execute(
            """
            INSERT INTO smartspend_wallet
                (user_id, total_income, total_budget, spent, balance, last_updated)
            VALUES (?, 0, 0, 0, 0, datetime('now','localtime'));
            """,
            (user_id,),
        )
        conn.commit()
        balance = 0.0
    else:
        balance = float(row[0] or 0.0)

    conn.close()
    return balance


def set_wallet_balance(value: float):
    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return

    cur.execute(
        """
        UPDATE smartspend_wallet
           SET balance = ?, last_updated = datetime('now','localtime')
         WHERE user_id = ?;
        """,
        (float(value), user_id),
    )

    if cur.rowcount == 0:
        cur.execute(
            """
            INSERT INTO smartspend_wallet
                (user_id, total_income, total_budget, spent, balance, last_updated)
            VALUES (?, 0, 0, 0, ?, datetime('now','localtime'));
            """,
            (user_id, float(value)),
        )

    conn.commit()
    conn.close()


def log_txn(
    tx_type,
    method,
    amount,
    source,
    target,
    category=None,
    item=None,
    remarks=None,
):
    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return

    cur.execute(
        """
        INSERT INTO transactions (
            user_id, date, type, method, category, item, amount, source, target, remarks
        )
        VALUES (
            ?, datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?
        );
        """,
        (user_id, tx_type, method, category, item, amount, source, target, remarks),
    )
    conn.commit()
    conn.close()


# ============================================================
#   GET USER EMAIL (NEW)
# ============================================================
def get_user_email() -> Optional[str]:
    """
    Fetch the current logged-in user's email from the users table.
    """
    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return None

    cur.execute("SELECT email FROM users WHERE id = ?;", (user_id,))
    row = cur.fetchone()
    conn.close()

    if row and row[0]:
        return row[0]
    return None
# ============================================================
#   BUDGET DATE FETCH
# ============================================================
def fetch_budget_dates():
    conn = get_conn()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return None, None

    cur = conn.cursor()
    cur.execute(
        """
        SELECT created_at, last_updated 
        FROM money_magic_budget 
        WHERE user_id = ?
        LIMIT 1;
        """,
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        start_date = row[0]
        end_date = row[1]
        return start_date, end_date
    return None, None


def calculate_progress(df):
    total_estimated = df["Estimated (RM)"].sum()
    total_actual = df["Actual (RM)"].sum()
    if total_estimated == 0:
        return 0.0
    return (total_actual / total_estimated) * 100


# ============================================================
#   MAIN PAGE
# ============================================================
def my_money_map_page():
    init_schema()
    apply_bg()

    # Ensure user is logged in
    conn = get_conn()
    user_id = get_current_user_id(conn)
    conn.close()
    if user_id is None:
        st.error("You must be logged in to use My Money Map.")
        return

    st.markdown(
        "<h1 style='color:#003366; text-align:center;'>🗺️ My Money Map 🗺️</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h2 style='color:#003366; text-align:center;'>My Money Tracker & SmartSpend Wallet</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    # ============================================================
    #   TRANSACTION HISTORY NAVIGATION
    # ============================================================
    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
    with nav_col1:
        if st.button("🏠 Return to Main Menu", use_container_width=True):
            st.session_state.page = "main_menu"
            st.rerun()
    with nav_col2:
        if st.button("🎯 Go to Money Magic", use_container_width=True):
            st.session_state.page = "money_magic"
            st.rerun()
    with nav_col3:
        if st.button("📜 Transaction History"):
            st.session_state.page = "transaction_history"
            st.rerun()

    # Fetch the budget start and end dates from the database
    start_date, end_date = fetch_budget_dates()

    if start_date and end_date:
        try:
            formatted_end_date = datetime.strptime(
                end_date, "%Y-%m-%d %H:%M:%S"
            ).strftime("%Y-%m-%d")
        except ValueError:
            formatted_end_date = end_date

        st.markdown(
            f"""
            <div style='background:rgba(5,87,112,0.92);
                        padding:18px 25px;
                        border-radius:12px;
                        box-shadow:0 3px 8px rgba(0,0,0,0.15);
                        font-size:18px;
                        width:fit-content;
                        color:#FFFFFF; font-weight:900;'>
                <div style='display:flex; justify-content:space-between; gap:80px;'>
                    <ul style='list-style-type:none; padding-left:0; margin:0; line-height:1.8;'>
                        <li><b>Budget Start Date:</b> {start_date}</li>
                    </ul>
                    <ul style='list-style-type:none; padding-left:0; margin:0; line-height:1.8;'>
                        <li><b>Budget End Date:</b> {formatted_end_date}</li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("No budget dates set yet. Please set up your budget in Money Magic.")

    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- Continue with Budget Table ---
    df = fetch_budget_df()
    if df.empty:
        st.warning("⚠️ No active budget found. Please set up your plan in Money Magic.")
        return

    income = float(get_income(user_id) or 0.0)
    est = df["Estimated (RM)"].sum()
    act = df["Actual (RM)"].sum()
    env = df["Envelope (RM)"].sum()
    wallet = get_wallet_balance()
    remaining = income - act

    st.markdown(
        f"""
    <div style='background:rgba(149,245,39,0.92);
                padding:18px 25px;
                border-radius:12px;
                box-shadow:0 3px 8px rgba(0,0,0,0.15);
                font-size:18px;
                width:fit-content;
                color:#032A44; font-weight:900;'>
        <div style='display:flex; justify-content:space-between; gap:80px;'>
            <ul style='list-style-type:none; padding-left:0; margin:0; line-height:1.8;'>
                <li><b>Budget Amount:</b> RM {income:,.2f}</li>
                <li><b>Actual Amount:</b> RM {act:,.2f}</li>
                <li><b>Estimated Amount:</b> RM {est:,.2f}</li>
            </ul>
            <ul style='list-style-type:none; padding-left:0; margin:0; line-height:1.8;'>
                <li><b>Available Total Balance:</b> RM {remaining:,.2f}</li>
                <li><b>Envelope Balance:</b> RM {env:,.2f}</li>
                <li><b>Wallet Balance:</b> RM {wallet:,.2f}</li>
            </ul>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ===== Budget Table =====
    st.markdown(
        "<br><h4 style='color:#003366;'>📊 My Money Tracker</h4>",
        unsafe_allow_html=True,
    )

    # Colour rules
    def color_payment_progress(val):
        val_str = str(val).lower()
        if val_str.startswith("fully"):
            return "background-color:#66bb6a; color:black; font-weight:bold;"
        if val_str.startswith("partially"):
            return "background-color:#ffa726; color:black; font-weight:bold;"
        if "over" in val_str:
            return "background-color:#d32f2f; color:white; font-weight:bold;"
        return "background-color:#F87C63; color:white; font-weight:bold;"

    def color_status(val):
        val_str = str(val).lower()
        if val_str == "completed":
            return "background-color:#66bb6a; color:black; font-weight:bold;"
        if val_str == "active":
            return "background-color:#FFFF00; color:black; font-weight:bold;"
        if val_str == "pending":
            return "background-color:#546e7a; color:white; font-weight:bold;"
        if val_str == "exceeded":
            return "background-color:#b71c1c; color:white; font-weight:bold;"
        return ""

    display_df = df.copy()
    num_cols = ["Estimated (RM)", "Actual (RM)", "Envelope (RM)"]
    for c in num_cols:
        display_df[c] = display_df[c].map(
            lambda x: f"{x:,.2f}" if pd.notnull(x) else "-"
        )

    styled_df = (
        display_df.style.applymap(color_payment_progress, subset=["Payment Progress"])
        .applymap(color_status, subset=["Status"])
    )

    st.markdown(
        "<div class='scroll-table'>" + styled_df.to_html(index=False) + "</div>",
        unsafe_allow_html=True,
    )

    # ============================================================
    #   EXPANDER DESIGNS (RESTORED)
    # ============================================================
    st.markdown(
        """
    <style>
        div[data-testid="stExpander"] {
            border-radius: 12px;
            border: 1px solid #c4d7ff;
            box-shadow: 0 3px 8px rgba(0,0,0,0.12);
            background: rgba(143,203,250,0.96);
            margin-bottom: 12px;
        }
        div[data-testid="stExpander"] > details > summary {
            padding: 12px 18px !important;
            background: linear-gradient(to right, #0975C8, #63B7F8);
            font-weight: 900;
            font-size: 16px;
            color: white;
            border-radius: 12px 12px 0 0;
            list-style: none;
            cursor: pointer;
        }
        div[data-testid="stExpander"] > details > summary::marker {
            display: none;
            content: "";
        }
        div[data-testid="stExpander"] > details > div {
            padding: 18px 20px 20px 20px;
            background: rgba(252,234,187,0.97);
            border-top: 1px solid #c4d7ff;
            border-radius: 0 0 12px 12px;
            animation: smartSpendFade 0.25s ease;
        }
        div[data-testid="stExpander"] > details > summary:hover {
            background: linear-gradient(to right, #079C1E, #63F879);
            transform: scale(1.005);
        }
        div[data-testid="stExpander"] > details > summary:after {
            content: "▼";
            float: right;
            font-size: 13px;
            color: #003366;
            transition: transform 0.25s ease;
            margin-left: 8px;
        }
        div[data-testid="stExpander"] > details[open] > summary:after {
            transform: rotate(-180deg);
        }
        @keyframes smartSpendFade {
            from { opacity: 0; transform: translateY(-3px); }
            to   { opacity: 1; transform: translateY(0); }
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # ============================================================
    #   SMARTSPEND WALLET
    # ============================================================
    st.markdown(
        "<br><h4 style='color:#003366;'>👛 SmartSpend Wallet</h4>",
        unsafe_allow_html=True,
    )
    wallet = get_wallet_balance()
    with st.expander("Click to Manage Wallet Functions", expanded=False):
        col1, col2, col3 = st.columns(3)

        # Top-Up
        with col1:
            top_amt = st.number_input(
                "Top-Up Amount (RM)", min_value=0.0, step=10.0, format="%.2f"
            )
            top_src = st.selectbox("Source", ["FPX", "E-WALLET (TNG)"])
            if st.button("➕ Top Up Wallet"):
                if top_amt > 0:
                    set_wallet_balance(wallet + top_amt)
                    log_txn(
                        "Top Up",
                        top_src,
                        top_amt,
                        source=top_src,
                        target="Wallet",
                        remarks="Wallet top-up (simulated)",
                    )
                    st.success(
                        f"Wallet topped up by RM {top_amt:.2f} via {top_src}."
                    )
                    time.sleep(0.5)
                    st.rerun()

        # Wallet → Envelope
        with col2:
            cat = st.selectbox("Category", df["Category"].unique())
            items = df[df["Category"] == cat]["Item"].tolist()
            item = st.selectbox("Item", items)
            amt = st.number_input(
                "Amount (RM)",
                min_value=0.0,
                step=10.0,
                format="%.2f",
                key="w_to_env",
            )
            if st.button("➡️ Wallet → Envelope 📩"):
                if amt <= 0:
                    st.warning("Enter an amount greater than RM 0.00.")
                elif amt > get_wallet_balance():
                    st.error("Insufficient wallet balance.")
                else:
                    set_wallet_balance(wallet - amt)
                    update_budget(cat, item, delta_env=amt)
                    log_txn(
                        "Transfer",
                        "Internal",
                        amt,
                        source="Wallet",
                        target="Envelope",
                        category=cat,
                        item=item,
                    )
                    st.success(f"Transferred RM {amt:.2f} to '{item}'.")
                    time.sleep(0.5)
                    st.rerun()

        # Envelope → Wallet
        with col3:
            cat2 = st.selectbox(
                "Category ", df["Category"].unique(), key="cat2"
            )
            items2 = df[df["Category"] == cat2]["Item"].tolist()
            item2 = st.selectbox("Item ", items2, key="item2")
            _, _, env_bal = fetch_line(cat2, item2)
            st.caption(f"Envelope balance: RM {env_bal:.2f}")
            amt2 = st.number_input(
                "Amount ",
                min_value=0.0,
                step=10.0,
                format="%.2f",
                key="amt2",
            )
            if st.button("⬅️ Envelope → Wallet 💵"):
                if amt2 > 0 and amt2 <= env_bal:
                    set_wallet_balance(wallet + amt2)
                    update_budget(cat2, item2, delta_env=-amt2)
                    log_txn(
                        "Transfer",
                        "Internal",
                        amt2,
                        source="Envelope",
                        target="Wallet",
                        category=cat2,
                        item=item2,
                    )
                    st.info("Funds returned to Wallet.")
                    time.sleep(0.5)
                    st.rerun()

    # ============================================================
    #   DUITNOW PAYMENT
    # ============================================================
    st.markdown(
        "<br><h4 style='color:#003366;'>💳 DuitNow Payment</h4>",
        unsafe_allow_html=True,
    )
    if "dn_open" not in st.session_state:
        st.session_state.dn_open = False
    if "dn_pending" not in st.session_state:
        st.session_state.dn_pending = None

    with st.expander("Click to Process DuitNow Payment", expanded=st.session_state.dn_open):
        p_cat = st.selectbox("Category (Payment)", df["Category"].unique())
        p_items = df[df["Category"] == p_cat]["Item"].tolist()
        p_item = st.selectbox("Item (Payment)", p_items)

        est_p, act_p, env_p = fetch_line(p_cat, p_item)
        st.caption(f"Envelope balance: RM {env_p:.2f} | Estimated: RM {est_p:.2f}")

        pay_amt = st.number_input(
            "Payment Amount (RM)", min_value=0.0, step=10.0, format="%.2f"
        )
        pay_note = st.text_input("Remarks", "Paid through SmartSpend")

        if st.button("💳 Make Payment"):
            if pay_amt <= 0:
                st.error("❌ Invalid payment amount.")
                st.stop()
            if pay_amt > env_p:
                st.error("❌ Insufficient envelope balance.")
                st.stop()

            if act_p + pay_amt > est_p:
                st.session_state.dn_open = True
                st.session_state.dn_pending = {
                    "cat": p_cat,
                    "item": p_item,
                    "amt": pay_amt,
                    "note": pay_note,
                    "est": est_p,
                }
                st.rerun()

            update_budget(p_cat, p_item, delta_actual=pay_amt, delta_env=-pay_amt)
            log_txn(
                "Payment",
                "DuitNow",
                pay_amt,
                "Envelope",
                "Merchant",
                p_cat,
                p_item,
                pay_note,
            )
            st.success(f"Paid RM {pay_amt:.2f} for '{p_item}'.")
            st.session_state.dn_open = False
            st.rerun()

        if st.session_state.dn_pending:
            p = st.session_state.dn_pending
            st.warning(
                f"⚠️ Your payment amount (RM {p['amt']:.2f}) exceeds "
                f"your budgeted amount (RM {p['est']:.2f})."
            )
            choice = st.radio(
                "Do you still want to proceed?",
                ["No", "Yes"],
                key="dn_confirm",
            )
            if choice == "Yes" and st.button("✔️ Confirm Exceeded Payment"):
                update_budget(
                    p["cat"], p["item"], delta_actual=p["amt"], delta_env=-p["amt"]
                )
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE money_magic_budget
                    SET status='Exceeded', payment_progress='Over Budget'
                    WHERE user_id = ? AND category = ? AND item_name = ?;
                    """,
                    (user_id, p["cat"], p["item"]),
                )
                conn.commit()
                conn.close()

                log_txn(
                    "Payment (Exceeded)",
                    "DuitNow",
                    p["amt"],
                    "Envelope",
                    "Merchant",
                    p["cat"],
                    p["item"],
                    p["note"],
                )

                # ===============================
                #   EMAIL ALERT: EXCEEDED PAYMENT
                # ===============================
                user_email = get_user_email()
                if user_email:
                    try:
                        est_after, act_after, env_after = fetch_line(p["cat"], p["item"])
                        exceeded_by = max(0.0, act_after - est_after)

                        subject = "SmartSpend Alert: Budget Exceeded (DuitNow Payment)"
                        body = (
                            f"Dear SmartSpend user,\n\n"
                            f"You have exceeded your budget for the following item:\n\n"
                            f"Category : {p['cat']}\n"
                            f"Item     : {p['item']}\n"
                            f"Budgeted : RM {est_after:,.2f}\n"
                            f"Actual   : RM {act_after:,.2f}\n"
                            f"Exceeded : RM {exceeded_by:,.2f}\n\n"
                            "This alert was generated automatically by SmartSpend My Money Map.\n\n"
                            "Best regards,\nSmartSpend System"
                        )
                        send_email(user_email, subject, body)
                    except Exception:
                        st.warning(
                            "Budget exceeded and recorded, but the email alert could not be sent."
                        )

                st.success(f"Exceeded payment of RM {p['amt']:.2f} processed.")
                st.session_state.dn_open = False
                st.session_state.dn_pending = None
                st.rerun()
            elif choice == "No" and st.button("✖️ Cancel Payment"):
                st.info("Payment cancelled.")
                st.session_state.dn_open = False
                st.session_state.dn_pending = None
                st.rerun()

    # ============================================================
    #   MANUAL WITHDRAWAL
    # ============================================================
    st.markdown(
        "<br><h4 style='color:#003366;'>🏧 Manual Withdrawal</h4>",
        unsafe_allow_html=True,
    )
    if "mw_open" not in st.session_state:
        st.session_state.mw_open = False
    if "mw_pending" not in st.session_state:
        st.session_state.mw_pending = None

    with st.expander(
        "Click to Record Manual Withdrawal", expanded=st.session_state.mw_open
    ):
        w_cat = st.selectbox("Category (Manual)", df["Category"].unique())
        w_items = df[df["Category"] == w_cat]["Item"].tolist()
        w_item = st.selectbox("Item (Manual)", w_items)

        est_m, act_m, env_m = fetch_line(w_cat, w_item)
        st.caption(f"Envelope balance: RM {env_m:.2f} | Estimated: RM {est_m:.2f}")

        w_amt = st.number_input(
            "Withdrawal Amount (RM)", min_value=0.0, step=10.0, format="%.2f"
        )
        w_note = st.text_input("Remarks", "Manual payment outside system")

        if st.button("🧾 Record Manual Withdrawal"):
            if w_amt <= 0:
                st.error("❌ Invalid withdrawal amount.")
                st.stop()
            if w_amt > env_m:
                st.error("❌ Insufficient envelope balance.")
                st.stop()

            if act_m + w_amt > est_m:
                st.session_state.mw_open = True
                st.session_state.mw_pending = {
                    "cat": w_cat,
                    "item": w_item,
                    "amt": w_amt,
                    "note": w_note,
                    "est": est_m,
                }
                st.rerun()

            update_budget(w_cat, w_item, delta_actual=w_amt, delta_env=-w_amt)
            log_txn(
                "Withdrawal",
                "Manual",
                w_amt,
                "Envelope",
                "—",
                category=w_cat,
                item=w_item,
                remarks=w_note,
            )
            st.success(
                f"Recorded manual withdrawal of RM {w_amt:.2f} for '{w_item}'."
            )
            st.session_state.mw_open = False
            st.rerun()

        if st.session_state.mw_pending:
            p = st.session_state.mw_pending
            st.warning(
                f"⚠️ Your withdrawal amount (RM {p['amt']:.2f}) exceeds "
                f"your budgeted amount (RM {p['est']:.2f})."
            )
            choice_mw = st.radio(
                "Do you still want to proceed with this withdrawal?",
                ["No", "Yes"],
                key="mw_confirm",
            )
            if choice_mw == "Yes" and st.button("✔️ Confirm Exceeded Withdrawal"):
                update_budget(
                    p["cat"], p["item"], delta_actual=p["amt"], delta_env=-p["amt"]
                )
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE money_magic_budget
                    SET status='Exceeded', payment_progress='Over Budget'
                    WHERE user_id = ? AND category = ? AND item_name = ?;
                    """,
                    (user_id, p["cat"], p["item"]),
                )
                conn.commit()
                conn.close()

                log_txn(
                    "Withdrawal (Exceeded)",
                    "Manual",
                    p["amt"],
                    "Envelope",
                    "—",
                    p["cat"],
                    p["item"],
                    p["note"],
                )

                # ===============================
                #   EMAIL ALERT: EXCEEDED WITHDRAWAL
                # ===============================
                user_email = get_user_email()
                if user_email:
                    try:
                        est_after, act_after, env_after = fetch_line(p["cat"], p["item"])
                        exceeded_by = max(0.0, act_after - est_after)

                        subject = "SmartSpend Alert: Budget Exceeded (Manual Withdrawal)"
                        body = (
                            f"Dear SmartSpend user,\n\n"
                            f"You have exceeded your budget for the following item:\n\n"
                            f"Category : {p['cat']}\n"
                            f"Item     : {p['item']}\n"
                            f"Budgeted : RM {est_after:,.2f}\n"
                            f"Actual   : RM {act_after:,.2f}\n"
                            f"Exceeded : RM {exceeded_by:,.2f}\n\n"
                            "This alert was generated automatically by SmartSpend My Money Map.\n\n"
                            "Best regards,\nSmartSpend System"
                        )
                        send_email(user_email, subject, body)
                    except Exception:
                        st.warning(
                            "Exceeded withdrawal recorded, but email failed to send."
                        )

                st.success(
                    f"Exceeded manual withdrawal of RM {p['amt']:.2f} processed."
                )
                st.session_state.mw_open = False
                st.session_state.mw_pending = None
                st.rerun()
            elif choice_mw == "No" and st.button("✖️ Cancel Withdrawal"):
                st.info("Withdrawal cancelled.")
                st.session_state.mw_open = False
                st.session_state.mw_pending = None
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
