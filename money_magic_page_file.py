#Author : Sharvena A/P Kumaran
#Student ID : 0128131
#FYP PROJECT 2025 UNIVERSITY OF WOLLONGONG MALAYSIA
#MoneyMagic File
# ===============================
# money_magic_page_file.py — Simple choose-and-save flow
# ===============================

# ---- Standard Library ----
import os
import io
import time
import base64
import sqlite3
from typing import Optional, Tuple
from datetime import datetime, date, timedelta

# ---- Third-Party ----
import pandas as pd
import streamlit as st
from datetime import datetime, date

# ---- ReportLab (PDF) ----
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image as RLImage,
)
from reportlab.lib.styles import getSampleStyleSheet

# ---- Shared DB PATH (same as login_register.py) ----
from repair_db_columns import DB_PATH

# ===============================
# Config (paths)
# ===============================
BG_PATH   = r"C:/Users/sharv/Downloads/UOW/FYP/FYP2/budget planner bg.jpg"
LOGO_PATH = r"C:/Users/sharv/Downloads/UOW/FYP/FYP2/smartspend_logo.png"

# ===============================
# Database Utilities
# ===============================
def get_conn():
    # Use the shared DB_PATH so every module points to the same database file
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def get_current_user_id(conn=None):
    """
    Returns the logged-in user's id (from users table) based on st.session_state.email.
    """
    email = getattr(st.session_state, "email", None)
    if not email:
        return None

    close_after = False
    if conn is None:
        conn = get_conn()
        close_after = True

    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?;", (email,))
    row = cur.fetchone()

    if close_after:
        conn.close()

    return row[0] if row else None


def ensure_base_schema():
    """Create tables if missing; add columns if needed."""
    conn = get_conn()
    cur = conn.cursor()

    # income
    cur.execute("""
        CREATE TABLE IF NOT EXISTS money_magic_income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monthly_income REAL DEFAULT 0,
            updated_at TEXT,
            user_id INTEGER
        );
    """)

    # budget
    cur.execute("""
        CREATE TABLE IF NOT EXISTS money_magic_budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            item_name TEXT,
            estimated_amount REAL,
            actual_amount REAL DEFAULT 0,
            envelope_balance REAL DEFAULT 0,
            payment_progress TEXT DEFAULT 'Not Paid',
            status TEXT DEFAULT 'Pending',
            confirmed INTEGER DEFAULT 0,
            created_at TEXT,
            last_updated TEXT,
            user_id INTEGER
        );
    """)

    # idempotent add columns (in case DB existed before)
    cur.execute("PRAGMA table_info(money_magic_budget);")
    cols = {r[1] for r in cur.fetchall()}
    needed = {
        "actual_amount": "REAL DEFAULT 0",
        "envelope_balance": "REAL DEFAULT 0",
        "payment_progress": "TEXT DEFAULT 'Not Paid'",
        "status": "TEXT DEFAULT 'Pending'",
        "confirmed": "INTEGER DEFAULT 0",
        "created_at": "TEXT",
        "last_updated": "TEXT",
        "user_id": "INTEGER",
    }
    for c, dtype in needed.items():
        if c not in cols:
            cur.execute(f"ALTER TABLE money_magic_budget ADD COLUMN {c} {dtype};")

    cur.execute("PRAGMA table_info(money_magic_income);")
    income_cols = {r[1] for r in cur.fetchall()}
    if "user_id" not in income_cols:
        cur.execute("ALTER TABLE money_magic_income ADD COLUMN user_id INTEGER;")

    conn.commit()
    conn.close()


ensure_base_schema()

# ===============================
# Theming / Background
# ===============================
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
    bg_style = f"""
        .stApp {{
            background: url("data:image/jpeg;base64,{b64}") no-repeat center center fixed;
            background-size: cover;
        }}
    """ if b64 else ""

    st.markdown(f"""
        <style>
            {bg_style}
            .blur-overlay {{
                position: fixed; inset: 0;
                backdrop-filter: blur(6px) brightness(0.93);
                z-index: -1;
            }}
            .card {{
                background: linear-gradient(to right,#ffffba,#baffc9,#bae1ff);
                color: #003366; font-weight: 600;
                padding: 18px; border-radius: 12px;
                margin: 8px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.15);
            }}
            /* Buttons style (match other pages) */
            div.stButton>button {{
                background: linear-gradient(to right,#ffffba,#baffc9,#bae1ff);
                color:#003366;
                border:none; border-radius:8px;
                padding:0.6em 1.5em;
                font-weight: 800 !important;
                letter-spacing: 0.3px; font-size:16px;
                cursor:pointer; transition:0.3s ease;
            }}
            div.stButton>button:hover {{
                filter:brightness(1.05); transform:scale(1.02);
            }}
            /* Expander styling */
            div[data-testid="stExpander"]{{
                background: rgba(7,156,17,0.98) !important;
                border: 1px solid #e6e6e6 !important;
                border-radius: 12px !important;
                box-shadow: 0 3px 10px rgba(0,0,0,0.08) !important;
                margin: 10px 0 12px 0 !important;
            }}
            div[data-testid="stExpander"] > details > summary{{
                background: rgba(5,112,12,0.98) !important;
                color: white;
                padding: 14px 18px !important;
            }}
            div[data-testid="stExpander"] > details > div{{
                background: rgba(187,252,191,1.0) !important;
                border-top: 1px solid #eee !important;
                padding: 14px 18px 18px 18px !important;
                border-bottom-left-radius: 12px !important;
                border-bottom-right-radius: 12px !important;
            }}
        </style>
        <div class="blur-overlay"></div>
    """, unsafe_allow_html=True)


def section_header(title: str):
    st.markdown(f"<div class='card'>{title}</div>", unsafe_allow_html=True)

# ===============================
# Data Helpers
# ===============================
def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_income() -> float:
    conn = get_conn()
    cur = conn.cursor()

    user_id = get_current_user_id(conn)
    if not user_id:
        conn.close()
        return 0.0

    try:
        cur.execute("""
            SELECT monthly_income
            FROM money_magic_income
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1;
        """, (user_id,))
        row = cur.fetchone()
    except Exception:
        conn.close()
        return 0.0

    conn.close()
    return float(row[0]) if row and row[0] is not None else 0.0


def set_income(value: float):
    conn = get_conn()
    cur = conn.cursor()

    user_id = get_current_user_id(conn)
    if not user_id:
        conn.close()
        return

    # Always clean previous records to avoid duplicates
    cur.execute("DELETE FROM money_magic_income WHERE user_id = ?;", (user_id,))

    cur.execute("""
        INSERT INTO money_magic_income (monthly_income, user_id, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP);
    """, (float(value), user_id))

    conn.commit()
    conn.close()


def add_budget_item(category: str, item_name: str, estimated_amount: float):
    """Upsert single item. amount > 0 creates/updates; amount == 0 deletes."""
    if not category or not item_name:
        return
    est = float(estimated_amount)

    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return
    cur.execute("""
        SELECT id FROM money_magic_budget
        WHERE user_id = ?
          AND TRIM(LOWER(category)) = TRIM(LOWER(?))
          AND TRIM(LOWER(item_name)) = TRIM(LOWER(?));
    """, (user_id, category, item_name))

    row = cur.fetchone()

    if row:
        # UPDATE only this specific row
        cur.execute("""
            UPDATE money_magic_budget
            SET estimated_amount = ?,
                last_updated = ?
            WHERE id = ?;
        """, (est, _now(), row[0]))
    else:
        # INSERT new row
        cur.execute("""
            INSERT INTO money_magic_budget
            (category, item_name, estimated_amount, actual_amount, envelope_balance,
             payment_progress, status, confirmed, created_at, last_updated, user_id)
            VALUES (?, ?, ?, 0, 0, 'Not Paid', 'Pending', 0, ?, ?, ?);
        """, (category, item_name, est, _now(), _now(), user_id))

    conn.commit()
    conn.close()


def delete_budget_item(category: str, item_name: str):
    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return
    cur.execute("""
        DELETE FROM money_magic_budget
         WHERE user_id = ?
           AND TRIM(LOWER(category)) = TRIM(LOWER(?))
           AND TRIM(LOWER(item_name)) = TRIM(LOWER(?));
    """, (user_id, category.strip(), item_name.strip()))
    conn.commit()
    conn.close()


def delete_items_by_prefix(category: str, item_prefix: str):
    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return

    cur.execute("""
        DELETE FROM money_magic_budget
         WHERE user_id = ?
           AND TRIM(LOWER(category)) = TRIM(LOWER(?))
           AND TRIM(LOWER(item_name)) LIKE TRIM(LOWER(?)) || '%';
    """, (user_id, category.strip(), item_prefix.strip()))

    conn.commit()
    conn.close()


def delete_items_by_contains(category: str, token: str):
    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return

    cur.execute("""
        DELETE FROM money_magic_budget
         WHERE user_id = ?
           AND TRIM(LOWER(category)) = TRIM(LOWER(?))
           AND INSTR(TRIM(LOWER(item_name)), TRIM(LOWER(?))) > 0;
    """, (user_id, category.strip(), token.strip()))

    conn.commit()
    conn.close()


def item_exists_in_db(category: str, item_name: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return False
    cur.execute("""
        SELECT 1 FROM money_magic_budget
        WHERE user_id = ?
          AND TRIM(LOWER(category)) = TRIM(LOWER(?))
          AND TRIM(LOWER(item_name)) LIKE TRIM(LOWER(?)) || '%'
        LIMIT 1;
    """, (user_id, category.lower(), item_name.lower()))

    exists = cur.fetchone() is not None
    conn.close()
    return exists


def _add_or_delete_by_amount(category: str, item_label: str, amount: float):
    """amount>0 -> upsert; amount==0 -> delete."""
    if amount and float(amount) > 0.0:
        add_budget_item(category, item_label, float(amount))
    else:
        delete_budget_item(category, item_label)


def fetch_budget_df() -> pd.DataFrame:
    conn = get_conn()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return pd.DataFrame()

    df = pd.read_sql_query("""
        SELECT
            category AS "Category",
            item_name AS "Item",
            estimated_amount AS "Estimated (RM)",
            actual_amount AS "Actual (RM)",
            status AS "Status",
            confirmed AS "Confirmed",
            created_at AS "Created"
        FROM money_magic_budget
        WHERE user_id = ?
        ORDER BY category, item_name;
    """, conn, params=(user_id,))
    conn.close()
    return df


def get_total_estimate() -> float:
    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return 0.0
    cur.execute("SELECT IFNULL(SUM(estimated_amount),0) FROM money_magic_budget WHERE user_id = ?;", (user_id,))
    val = cur.fetchone()[0] or 0.0
    conn.close()
    return float(val)


def _set_status_and_progress(est: float, act: float) -> Tuple[str, str]:
    if act <= 0:
        return "Pending", "Not Paid"
    if act < est:
        return "Active", "Partially Paid"
    if act == est:
        return "Completed", "Fully Paid"
    return "Exceeded", "Fully Paid"


def validate_budget_balance() -> Tuple[float, float, bool]:
    """Returns (total_est, income, over_budget). Also shows notices."""
    income = get_income()
    total_est = get_total_estimate()
    if total_est == 0:
        return 0.0, income, False
    if income > 0:
        if total_est > income:
            over_amount = total_est - income
            st.error(
                f"⚠️ Your total planned budget (RM {total_est:,.2f}) "
                f"exceeds your income (RM {income:,.2f}) by RM {over_amount:,.2f}. "
                "Please adjust before saving."
            )
            return total_est, income, True
        else:
            st.success(
                f"✅ Planned budget (RM {total_est:,.2f}) is within income (RM {income:,.2f})."
            )
    return total_est, income, total_est > income

# ===============================
# PDF Download Helper
# ===============================
def offer_pdf_download(df_budget: pd.DataFrame, income: float, start_date: date, end_date: date, logo_path: str):
    """Generate a PDF summary and render a Streamlit download button."""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        if logo_path and os.path.exists(logo_path):
            elements.append(RLImage(logo_path, width=100, height=50))
            elements.append(Spacer(1, 12))

        elements.append(Paragraph("<b>SMARTSPEND — Budget Summary Report</b>", styles["Title"]))
        elements.append(Spacer(1, 12))

        info = Paragraph(
            f"<b>Period:</b> {start_date} → {end_date}<br/>"
            f"<b>Total Income:</b> RM {income:,.2f}<br/><br/>",
            styles["Normal"],
        )
        elements.append(info)
        elements.append(Spacer(1, 10))

        data = [["Category", "Item", "Estimated (RM)", "Actual (RM)", "Status", "Confirmed"]]
        for _, row in df_budget.iterrows():
            data.append([
                row["Category"],
                row["Item"],
                f"{row['Estimated (RM)']:.2f}" if pd.notnull(row["Estimated (RM)"]) else "-",
                f"{row['Actual (RM)']:.2f}" if pd.notnull(row["Actual (RM)"]) else "-",
                row["Status"] if pd.notnull(row["Status"]) else "-",
                "Yes" if int(row.get("Confirmed", 0) or 0) == 1 else "No",
            ])

        table = Table(data, colWidths=[90, 130, 80, 80, 80, 60])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("<i>Generated automatically by SmartSpend Budget Tracker © 2025</i>",
                                  styles["Normal"]))

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()

        st.download_button(
            label="📄 Download Budget Summary (PDF)",
            data=pdf_data,
            file_name=f"Budget_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        st.warning(f"⚠️ Could not generate PDF: {e}")

# ===============================
# Input helpers
# ===============================
def _num_items(label: str, min_v=1, max_v=5, key=None):
    return st.number_input(label, min_value=min_v, max_value=max_v, step=1, key=key)


def _amount(label: str, key=None):
    return st.number_input(label, min_value=0.0, step=1.0, key=key)

# ===============================
# Categories (12) — simple, no auto-delete on uncheck
# Unchecking a checkbox does not delete; only amount=0 deletes.
# ===============================

# --- Category 1 — Instalments / Rental ---
def cat_instalments():
    with st.expander("Category 1 — Instalments / Rental", expanded=False):
        if st.checkbox("Home instalment/rental?", key="c1_home_yes"):
            n = _num_items("How many homes?", key="c1_home_n")
            for i in range(1, n + 1):
                label = f"Home #{i}"
                amt = _amount(f"{label} amount (RM)", key=f"c1_home_amt_{i}")
                _add_or_delete_by_amount("Instalments / Rental", label, amt)
        else:
            pass  # no auto-delete

        if st.checkbox("Vehicle instalment?", key="c1_vehicle_yes"):
            n = _num_items("How many vehicles?", key="c1_vehicle_n")
            for i in range(1, n + 1):
                label = f"Vehicle #{i}"
                amt = _amount(f"{label} amount (RM)", key=f"c1_vehicle_amt_{i}")
                _add_or_delete_by_amount("Instalments / Rental", label, amt)
        else:
            pass

        if st.checkbox("Other instalments?", key="c1_other_yes"):
            n = _num_items("How many others?", key="c1_other_n")
            for i in range(1, n + 1):
                name = st.text_input(f"Other #{i} name", key=f"c1_other_name_{i}")
                amt  = _amount(f"Other #{i} amount (RM)", key=f"c1_other_amt_{i}")
                if name:
                    _add_or_delete_by_amount("Instalments / Rental", name.strip(), amt)
        else:
            pass

# --- Category 2 — Loans ---
def _loans_multi_toggle(name_prefix: str, label: str):
    key_base = f"c2_{name_prefix}"
    if st.checkbox(f"{label}?", key=f"{key_base}_yes"):
        n = _num_items("How many accounts?", key=f"{key_base}_n")
        for i in range(1, n + 1):
            item = f"{label} #{i}"
            amt  = _amount(f"{item} amount (RM)", key=f"{key_base}_amt_{i}")
            _add_or_delete_by_amount("Loans", item, amt)
    else:
        pass


def cat_loans():
    with st.expander("Category 2 — Loans", expanded=False):
        _loans_multi_toggle("pl", "Personal Loan")
        _loans_multi_toggle("cc", "Credit Card Loan")
        _loans_multi_toggle("ptptn", "PTPTN / Study Loan")

        if st.checkbox("LazPayLater?", key="c2_laz_yes"):
            amt = _amount("LazPayLater amount (RM)", key="c2_laz_amt")
            _add_or_delete_by_amount("Loans", "LazPayLater", amt)
        if st.checkbox("ShopeePayLater?", key="c2_shop_yes"):
            amt = _amount("ShopeePayLater amount (RM)", key="c2_shop_amt")
            _add_or_delete_by_amount("Loans", "ShopeePayLater", amt)

        if st.checkbox("Other loans?", key="c2_other_yes"):
            n = _num_items("How many others?", key="c2_other_n")
            for i in range(1, n + 1):
                name = st.text_input(f"Other Loan #{i} name", key=f"c2_other_name_{i}")
                amt  = _amount(f"Other Loan #{i} amount (RM)", key=f"c2_other_amt_{i}")
                if name:
                    _add_or_delete_by_amount("Loans", name.strip(), amt)
        else:
            pass

# --- Category 3 — Bills & Utilities ---
def _bills_toggle(title: str, key_prefix: str):
    key_base = f"c3_{key_prefix}"
    if st.checkbox(f"{title}?", key=f"{key_base}_yes"):
        n = _num_items("How many accounts?", key=f"{key_base}_n")
        for i in range(1, n + 1):
            item = f"{title} #{i}"
            amt  = _amount(f"{item} amount (RM)", key=f"{key_base}_amt_{i}")
            _add_or_delete_by_amount("Bills & Utilities", item, amt)
    else:
        pass


def cat_bills():
    with st.expander("Category 3 — Bills and Utilities", expanded=False):
        _bills_toggle("Syabas (Water)", "syabas")
        _bills_toggle("TNB (Electric)", "tnb")
        _bills_toggle("IndahWater", "iwk")
        _bills_toggle("Internet Bill", "internet")
        _bills_toggle("Postpaid Bill", "postpaid")
        _bills_toggle("Prepaid Bill", "prepaid")

        if st.checkbox("Other bills?", key="c3_other_yes"):
            n = _num_items("How many others?", key="c3_other_n")
            for i in range(1, n + 1):
                name = st.text_input(f"Other Bill #{i} name", key=f"c3_other_name_{i}")
                amt  = _amount(f"Other Bill #{i} amount (RM)", key=f"c3_other_amt_{i}")
                if name:
                    _add_or_delete_by_amount("Bills & Utilities", name.strip(), amt)
        else:
            pass

# --- Category 4 — Entertainment ---
def cat_entertainment():
    with st.expander("Category 4 — Entertainment", expanded=False):
        services = [
            "Astro","Netflix","Amazon Prime Video","Disney Hotstar","Apple TV",
            "Spotify","YouTube Premium","YouTube Music Premium","ChatGPT",
        ]
        for svc in services:
            key = f"c4_{svc}"
            if st.checkbox(f"{svc}?", key=f"{key}_yes"):
                n = _num_items("How many accounts?", key=f"{key}_n")
                for i in range(1, n + 1):
                    item = f"{svc} #{i}"
                    amt  = _amount(f"{item} amount (RM)", key=f"{key}_amt_{i}")
                    _add_or_delete_by_amount("Entertainment", item, amt)
            else:
                pass

        if st.checkbox("Other entertainment?", key="c4_other_yes"):
            n = _num_items("How many others?", key="c4_other_n")
            for i in range(1, n + 1):
                name = st.text_input(f"Other Entertainment #{i} name", key=f"c4_other_name_{i}")
                amt  = _amount(f"Other Entertainment #{i} amount (RM)", key=f"c4_other_amt_{i}")
                if name:
                    _add_or_delete_by_amount("Entertainment", name.strip(), amt)
        else:
            pass

# --- Category 5 — Household ---
def cat_household():
    with st.expander("Category 5 — Household", expanded=False):
        simple = [
            "Groceries","Dry Groceries","Wet Groceries","Part time Cleaner",
            "In house Maid","Laundry","Catering Food","Dine out",
        ]
        for s in simple:
            key = f"c5_{s}"
            if st.checkbox(f"{s}?", key=f"{key}_yes"):
                amt = _amount(f"{s} amount (RM)", key=f"{key}_amt")
                _add_or_delete_by_amount("Household", s, amt)
            else:
                pass

        if st.checkbox("Other household items?", key="c5_other_yes"):
            n = _num_items("How many others?", key="c5_other_n")
            for i in range(1, n + 1):
                name = st.text_input(f"Other Household #{i} name", key=f"c5_other_name_{i}")
                amt  = _amount(f"Other Household #{i} amount (RM)", key=f"c5_other_amt_{i}")
                if name:
                    _add_or_delete_by_amount("Household", name.strip(), amt)
        else:
            pass

# --- Category 6 — Transport (Fuel/Transit) ---
def cat_transport():
    with st.expander("Category 6 — Vehicle Gas (Petrol / Diesel / Transport)", expanded=False):
        # Budi95 or Non-subsidised — no auto-delete of the alternative
        if st.checkbox("Use Budi95 subsidy for RON95?", key="c6_budi95_yes"):
            opt    = st.selectbox("Select Budi95 option", ["300 litres","800 litres"], key="c6_budi95_opt")
            cap    = 300 if opt.startswith("300") else 800
            litres = st.number_input("Enter total RON95 litres (per month)", min_value=0.0, step=1.0,
                                     key="c6_budi95_litres")
            cost   = (min(litres, cap) * 1.99) + (max(0.0, litres - cap) * 2.60) if litres else 0.0
            label  = f"RON95 (Budi95 {cap}L)"
            _add_or_delete_by_amount("Transport", label, cost)
            st.caption(f"Calculated: RM {cost:,.2f}" if litres else "No litres entered.")

        if st.checkbox("RON95 (no subsidy)?", key="c6_ron95_yes"):
            litres = st.number_input("RON95 litres (no subsidy)", min_value=0.0, step=1.0, key="c6_ron95_litres")
            total_ron95 = litres * 2.60 if litres else 0.0
            _add_or_delete_by_amount("Transport", "RON95 (no subsidy)", total_ron95)

        if st.checkbox("RON97?", key="c6_ron97_yes"):
            litres = st.number_input("RON97 litres", min_value=0.0, step=1.0, key="c6_ron97_litres")
            total_ron97 = litres * 3.20 if litres else 0.0
            _add_or_delete_by_amount("Transport", "RON97", total_ron97)

        if st.checkbox("Diesel?", key="c6_diesel_yes"):
            region = st.selectbox("Region", ["Peninsular Malaysia","East Malaysia"], key="c6_diesel_region")
            litres = st.number_input("Diesel litres", min_value=0.0, step=1.0, key="c6_diesel_litres")
            price  = 3.02 if region == "Peninsular Malaysia" else 2.15
            total_diesel = litres * price if litres else 0.0
            _add_or_delete_by_amount("Transport", f"Diesel ({region})", total_diesel)

        if st.checkbox("General petrol allocation?", key="c6_general_yes"):
            amt = _amount("Allocation amount (RM)", key="c6_general_amt")
            _add_or_delete_by_amount("Transport", "General Petrol Allocation", amt)

        if st.checkbox("Public/other transport modes?", key="c6_modes_yes"):
            modes = ["GrabCar","Taxi","KTM Komuter","LRT","MRT","BRT","Monorail","Bus"]
            for m in modes:
                if st.checkbox(m, key=f"c6_mode_{m}"):
                    amt = _amount(f"{m} allocation (RM)", key=f"c6_mode_amt_{m}")
                    _add_or_delete_by_amount("Transport", m, amt)
        else:
            pass

# --- Category 7 — Personal ---
def cat_personal():
    with st.expander("Category 7 — Personal", expanded=False):
        items = [
            "Insurance","Medicines","Allowance",
            "Vehicle Insurance","Fire Insurance","Home Insurance","Business Insurance",
        ]
        for s in items:
            key = f"c7_{s}"
            if st.checkbox(f"{s}?", key=f"{key}_yes"):
                if s in {"Vehicle Insurance","Home Insurance","Business Insurance"}:
                    n = _num_items("How many?", key=f"{key}_n")
                    for i in range(1, n + 1):
                        label = f"{s} #{i}"
                        amt   = _amount(f"{label} amount (RM)", key=f"{key}_amt_{i}")
                        _add_or_delete_by_amount("Personal", label, amt)
                else:
                    amt = _amount(f"{s} amount (RM)", key=f"{key}_amt")
                    _add_or_delete_by_amount("Personal", s, amt)
            else:
                pass

        if st.checkbox("Other personal items?", key="c7_other_yes"):
            n = _num_items("How many?", key="c7_other_n")
            for i in range(1, n + 1):
                name = st.text_input(f"Other Personal #{i} name", key=f"c7_other_name_{i}")
                amt  = _amount(f"Other Personal #{i} amount (RM)", key=f"c7_other_amt_{i}")
                if name:
                    _add_or_delete_by_amount("Personal", name.strip(), amt)
        else:
            pass

# --- Category 8 — Family ---
def cat_family():
    with st.expander("Category 8 — Family", expanded=False):
        if st.checkbox("Include family-related allocations?", key="c8_yes"):
            # Spouse
            if st.checkbox("Spouse", key="c8_spouse"):
                for f in ["Insurance","Medicines","Allowance"]:
                    if st.checkbox(f"Spouse {f}?", key=f"c8_spouse_{f}"):
                        amt = _amount(f"Spouse {f} amount (RM)", key=f"c8_spouse_{f}_amt")
                        _add_or_delete_by_amount("Family", f"Spouse {f}", amt)
            # Child
            if st.checkbox("Child", key="c8_child"):
                nchild = _num_items("Number of children", max_v=10, key="c8_child_n")
                child_fields = [
                    "Insurance","Medicines","Allowance","Nursery care","Kindergarten",
                    "School fees","Tuition fees","Transport fees","Tertiary Education fees"
                ]
                for f in child_fields:
                    if st.checkbox(f"{f}?", key=f"c8_child_{f}"):
                        for i in range(1, nchild + 1):
                            label = f"Child #{i} — {f}"
                            amt   = _amount(f"{label} amount (RM)", key=f"c8_child_{f}_amt_{i}")
                            _add_or_delete_by_amount("Family", label, amt)
            # Parents
            if st.checkbox("Parents", key="c8_parents"):
                who = st.selectbox("Who?", ["Mother","Father","Mother and Father"], key="c8_parent_who")
                parent_targets = ["Insurance","Medicines","Allowance","Caretaker","Nurse","Genesis care"]
                for f in parent_targets:
                    if st.checkbox(f"{f}?", key=f"c8_par_{f}"):
                        targets = ["Mother","Father"] if who == "Mother and Father" else [who]
                        for t in targets:
                            label = f"{t} — {f}"
                            amt   = _amount(f"{label} amount (RM)", key=f"c8_par_{f}_{t}_amt")
                            _add_or_delete_by_amount("Family", label, amt)
            # Siblings
            if st.checkbox("Siblings", key="c8_siblings"):
                nsib = _num_items("Number of siblings", max_v=10, key="c8_sib_n")
                for f in ["Insurance","Medicines","Allowance"]:
                    if st.checkbox(f"{f}?", key=f"c8_sib_{f}"):
                        for i in range(1, nsib + 1):
                            label = f"Sibling #{i} — {f}"
                            amt   = _amount(f"{label} amount (RM)", key=f"c8_sib_{f}_{i}_amt")
                            _add_or_delete_by_amount("Family", label, amt)
            # Others
            if st.checkbox("Other relationships?", key="c8_others"):
                n = _num_items("How many?", key="c8_others_n")
                for i in range(1, n + 1):
                    relation = st.text_input(f"Other #{i} relationship", key=f"c8_other_rel_{i}")
                    amt      = _amount(f"Other #{i} amount (RM)", key=f"c8_other_amt_{i}")
                    if relation:
                        _add_or_delete_by_amount("Family", f"Other — {relation.strip()}", amt)
        else:
            pass

# --- Category 9 — Tax ---
def cat_tax():
    with st.expander("Category 9 — Tax", expanded=False):
        items = ["Cukai Tanah","Cukai Pintu","Personal Income Tax","Road Tax","Corporate Income Tax","Zakat"]
        for s in items:
            key = f"c9_{s}"
            if s == "Road Tax":
                if st.checkbox(f"{s}?", key=f"{key}_yes"):
                    n = _num_items("Number of vehicles", key="c9_rt_n")
                    for i in range(1, n + 1):
                        label = f"Road Tax #{i}"
                        amt   = _amount(f"{label} amount (RM)", key=f"c9_rt_amt_{i}")
                        _add_or_delete_by_amount("Tax", label, amt)
            else:
                if st.checkbox(f"{s}?", key=f"{key}_yes"):
                    amt = _amount(f"{s} amount (RM)", key=f"{key}_amt")
                    _add_or_delete_by_amount("Tax", s, amt)

        if st.checkbox("Other taxes?", key="c9_other_yes"):
            n = _num_items("How many?", key="c9_other_n")
            for i in range(1, n + 1):
                name = st.text_input(f"Other Tax #{i} name", key=f"c9_other_name_{i}")
                amt  = _amount(f"Other Tax #{i} amount (RM)", key=f"c9_other_amt_{i}")
                if name:
                    _add_or_delete_by_amount("Tax", name.strip(), amt)
        else:
            pass

# --- Category 10 — Luxury ---
def cat_luxury():
    with st.expander("Category 10 — Luxury", expanded=False):
        items = ["Vacation","Expensive Jewellery","Movie Theatre","Entertainment Live Shows and Concerts","Fine Dining"]
        for s in items:
            key = f"c10_{s}"
            if st.checkbox(f"{s}?", key=f"{key}_yes"):
                amt = _amount(f"{s} amount (RM)", key=f"{key}_amt")
                _add_or_delete_by_amount("Luxury", s, amt)
        if st.checkbox("Other luxury items?", key="c10_other_yes"):
            n = _num_items("How many?", key="c10_other_n")
            for i in range(1, n + 1):
                name = st.text_input(f"Other Luxury #{i} name", key=f"c10_other_name_{i}")
                amt  = _amount(f"Other Luxury #{i} amount (RM)", key=f"c10_other_amt_{i}")
                if name:
                    _add_or_delete_by_amount("Luxury", name.strip(), amt)
        else:
            pass

# --- Category 11 — Savings ---
def cat_savings():
    with st.expander("Category 11 — Savings", expanded=False):
        items = ["Personal Savings","Investments","Fixed Deposit Savings (FD)","Self contribution EPF","Spouse contribution EPF"]
        for s in items:
            key = f"c11_{s}"
            if st.checkbox(f"{s}?", key=f"{key}_yes"):
                amt = _amount(f"{s} amount (RM)", key=f"{key}_amt")
                _add_or_delete_by_amount("Savings", s, amt)
        if st.checkbox("Other savings?", key="c11_other_yes"):
            n = _num_items("How many?", key="c11_other_n")
            for i in range(1, n + 1):
                name = st.text_input(f"Other Savings #{i} name", key=f"c11_other_name_{i}")
                amt  = _amount(f"Other Savings #{i} amount (RM)", key=f"c11_other_amt_{i}")
                if name:
                    _add_or_delete_by_amount("Savings", name.strip(), amt)
        else:
            pass

# --- Category 12 — Custom Others ---
def cat_custom():
    with st.expander("Category 12 — Others (Custom)", expanded=False):
        if st.checkbox("Create custom categories?", key="c12_yes"):
            n = _num_items("How many custom items?", key="c12_n")
            for i in range(1, n + 1):
                name = st.text_input(f"Custom Item #{i} name", key=f"c12_name_{i}")
                amt  = _amount(f"Custom Item #{i} amount (RM)", key=f"c12_amt_{i}")
                if name:
                    _add_or_delete_by_amount("Others", name.strip(), amt)
        else:
            pass


# Function to reset budget and clear existing data
def clear_existing_budget():
    # Clear the session state for budget data
    st.session_state.budget = {}
    st.session_state.categories = {}
    st.session_state.budget_saved = False

    conn = get_conn()
    cur = conn.cursor()
    user_id = get_current_user_id(conn)
    if user_id is not None:
        cur.execute("DELETE FROM money_magic_budget WHERE user_id = ?;", (user_id,))
    conn.commit()
    conn.close()


# ===============================
# Main Page
# ===============================
    # Money Magic Page - Only add the date functionality without changing current flow

def money_magic_page():
    apply_bg()

    st.markdown("""
    <style>
    /* SUPER BOLD LABELS TO MATCH INPUT STYLE */
    label, 
    .stTextInput label, 
    .stNumberInput label, 
    .stDateInput label {
        font-size: 40px !important;
        font-weight: 1000 !important;  /* Stronger than 900 */
        color: #00264d !important;     /* Deeper SmartSpend blue */
        margin-bottom: 10px !important;
        letter-spacing: 0.4px !important;
    }

    /* Number input main container */
    div[data-testid="stNumberInput"] > div:first-child {
        background: rgba(5,87,112,0.95) !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 25px !important;
        padding: 10px !important;
    }

    /* The actual number text box */
    div[data-testid="stNumberInput"] input {
        background: transparent !important;
        color: #FFFFFF !important;
        font-size: 25px !important;
        font-weight: 700 !important;
    }

    /* The + and - buttons container */
    div[data-testid="stNumberInput"] button {
        background: rgba(5,87,112,0.95) !important;
        border-radius: 10px !important;
        border: 1px solid #FFFFFF !important;
        color: #FFFFFF !important;
        font-weight: 900 !important;
    }

    /* Hover effect for the buttons */
    div[data-testid="stNumberInput"] button:hover {
        background: #247005 !important;
        border-color: #80aaff !important;
    }

    /* Entire date input container */
    div[data-baseweb="input"] {
        background: rgba(5,87,112,0.95) !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 25px !important;
        padding: 6px !important;
        box-shadow: none !important;
    }

    /* Inner date input element */
    div[data-baseweb="input"] > div {
        background: transparent !important;  
        border: none !important;
        border-radius: 20px !important;
    }

    /* Text inside the date input */
    div[data-baseweb="input"] input {
        background: transparent !important;
        font-size: 25px !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        padding: 12px !important;
    }

    /* Calendar icon */
    div[data-baseweb="input"] svg {
        fill: #003366 !important;
        width: 28px !important;
        height: 28px !important;
    }
    
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <style>

        /* OUTER DATE INPUT CONTAINER */
        div[data-testid="stDateInput"] > div {
            max-width: 300px !important;     /* Box width */
            height: 40px !important;          /* Adjust height here */
            border-radius: 18px !important;
            display: flex !important;
            align-items: center !important;
            padding: 4px 10px !important;
        }

        /* INNER INPUT FIELD */
        div[data-testid="stDateInput"] input {
            height: 35px !important;          /* Actual input height */
            line-height: 45px !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            padding: 0 12px !important;
        }

    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <style>

        /* =====================================================
           MERGE +/- BUTTONS INTO THE SAME PILL CONTAINER
           ===================================================== */

        /* The minus and plus buttons */
        button[data-testid="baseButton-secondary"] {
            background-color: #085b73 !important;     /* same teal */
            color: white !important;
            border: 3px solid #a3d9ff !important;     /* same border */
            border-radius: 0px !important;            /* remove curve */
            height: 70px !important;                  /* match pill height */
            width: 70px !important;
            font-size: 28px !important;
            font-weight: bold !important;
            margin-left: -4px !important;             /* overlap tiny gap */
        }

        /* Round ONLY the rightmost button */
        button[data-testid="baseButton-secondary"]:last-child {
            border-top-right-radius: 45px !important;
            border-bottom-right-radius: 45px !important;
        }

        /* Round ONLY the left input side */
        div[data-testid="stNumberInput"] > div {
            border-top-left-radius: 45px !important;
            border-bottom-left-radius: 45px !important;
            margin-right: -4px !important;            /* eliminate gap */
        }

    </style>
    """, unsafe_allow_html=True)

    # Step 1 — Income (no change)
    st.markdown("<h1 style='text-align:center;color:#003366;'>💰MoneyMagic💰</h1>", unsafe_allow_html=True)
    current_income = get_income()
    new_income = st.number_input("Budget Amount (RM)", min_value=0.0, step=100.0,
                                 value=float(current_income) if current_income else 0.0)

    if st.button("💾 Save Budget Amount", use_container_width=True):
        set_income(new_income)
        st.success("Budget Amount saved successfully.")
        time.sleep(0.2)
        st.rerun()

    # Money Magic Page: Save Dates
    start_date = st.date_input("Start Date", value=datetime.today())
    end_date = st.date_input("End Date", value=datetime.today() + timedelta(days=30))

    # Save Start and End Dates when Save Budget is clicked
    if st.button("💾 Save Budget Dates", use_container_width=True):
        user_id = get_current_user_id()
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            UPDATE money_magic_budget
            SET created_at = ?, last_updated = ?
            WHERE user_id = ?
        """, (start_date, end_date, user_id))

        conn.commit()
        conn.close()

        # Store as strings in session state
        st.session_state.tracker_start_dt = str(start_date)
        st.session_state.tracker_end_dt = str(end_date)

        st.success(f"Budget duration saved from {start_date} to {end_date}.")
        time.sleep(0.2)
        st.rerun()

    # Step 2 — Categories
    st.markdown("<h4 style='color:#003366;'>Setup Your Budget</h4>",
                unsafe_allow_html=True)
    st.markdown("<h6 style='color:#05700C;'>Choose Expense Categories & Enter Estimated Amounts</h6>",
                unsafe_allow_html=True)
    st.info("Set each amount. Setting an amount to 0 will remove that line from your plan.")

    # Non-blocking validation banners (will update live)
    total_est, income, over_budget = validate_budget_balance()

    # 12 categories
    cat_instalments()
    cat_loans()
    cat_bills()
    cat_entertainment()
    cat_household()
    cat_transport()
    cat_personal()
    cat_family()
    cat_tax()
    cat_luxury()
    cat_savings()
    cat_custom()

    # ============================
    # Preview + PDF (bottom)
    # ============================
    st.markdown("<hr style='border: 0.5px solid #181601; margin: 30px 0;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#003366;'>Preview of Your Budget Plan</h4>", unsafe_allow_html=True)
    st.markdown(
        "<h6 style='color:#05700C;'>Review planned categories, items, and estimated amounts. Then save your plan.</h6>",
        unsafe_allow_html=True)

    # Example function to simulate fetching dates from the database
    def fetch_budget_dates():
        # Simulate retrieved dates with time
        start_date = "2025-11-18"
        end_date = "2025-12-18 02:20:35"  # Example with time included
        return start_date, end_date

    # Fetch the budget start and end dates from the database
    start_date, end_date = fetch_budget_dates()

    # Format the dates to show only the date portion (ignoring time)
    if start_date and end_date:
        try:
            # If the end_date includes time, we strip the time part
            formatted_end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        except ValueError:
            formatted_end_date = end_date  # In case it's already in the correct format

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
            """, unsafe_allow_html=True
        )
    else:
        st.warning("No budget dates set yet. Please set up your budget in Money Magic.")
        st.markdown("<br><br>", unsafe_allow_html=True)
    try:
        df_preview = fetch_budget_df()

        if not df_preview.empty:

            df_display = df_preview.copy()

            # Friendly numeric formatting
            for col in ["Estimated (RM)", "Actual (RM)"]:
                if col in df_display.columns:
                    df_display[col] = df_display[col].map(
                        lambda x: f"{x:,.2f}" if pd.notnull(x) else "-"
                    )

            # Confirmed → Yes/No
            if "Confirmed" in df_display.columns:
                df_display["Confirmed"] = df_display["Confirmed"].map(
                    lambda v: "Yes" if int(v or 0) == 1 else "No"
                )

            # ---------- Colour Functions ----------
            def color_confirmation(val):
                if val == "Yes":
                    return "background-color:#66bb6a; color:black; font-weight:bold;"
                return "background-color:#ef9a9a; color:white; font-weight:bold;"

            def color_status(val):
                x = str(val).lower()
                if "completed" in x:
                    return "background-color:#66bb6a; color:black; font-weight:bold;"
                if "active" in x:
                    return "background-color:#ffa726; color:black; font-weight:bold;"
                if "pending" in x:
                    return "background-color:#90a4ae; color:black; font-weight:bold;"
                if "exceeded" in x:
                    return "background-color:#ef5350; color:white; font-weight:bold;"
                return ""

            # Full-row highlight for Exceeded
            def highlight_exceeded(row):
                if "Exceeded" in str(row.get("Status", "")):
                    return ["background-color:#fdecea;" for _ in row]
                return [""] * len(row)

            # ---------- Apply Table Style ----------
            styled_df = (
                df_display.style
                .set_table_styles(
                    [
                        {"selector": "th",
                         "props": [
                             ("background-color", "#003366"),
                             ("color", "white"),
                             ("font-weight", "bold"),
                             ("text-align", "center"),
                             ("padding", "8px")
                         ]},
                        {"selector": "td",
                         "props": [
                             ("padding", "6px"),
                             ("border", "0.5px solid #e0e0e0")
                         ]},
                        {
                            "selector": "tbody tr",
                            "props": [("background-color", "#BBF0FC")]
                        },
                    ]
                )
                .apply(highlight_exceeded, axis=1)
            )

            # Apply confirmation colors
            if "Confirmed" in df_display.columns:
                styled_df = styled_df.applymap(color_confirmation, subset=["Confirmed"])

            # Apply status colors
            if "Status" in df_display.columns:
                styled_df = styled_df.applymap(color_status, subset=["Status"])

            # Display styled table
            st.markdown("<div class='scroll-table'>", unsafe_allow_html=True)
            st.write(styled_df.to_html(index=False), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ==== Budget Summary After Preview Table ====
            total_est = df_preview["Estimated (RM)"].sum() if "Estimated (RM)" in df_preview else 0
            total_act = df_preview["Actual (RM)"].sum() if "Actual (RM)" in df_preview else 0
            difference = total_est - total_act

            st.markdown("""
                <div style='background:rgba(252,244,187,0.85);
                            padding:15px; border-radius:12px;
                            box-shadow:0 3px 8px rgba(0,0,0,0.12);
                            width:60%; margin:auto;'>
                    <h4 style='color:#003366; text-align:center; margin-bottom:10px;'>💰 Budget Summary</h4>
                    <table style='width:100%; font-size:16px;'>
                        <tr>
                            <td><b>Total Estimated Expenses:</b></td>
                            <td style='text-align:right;'>RM {est:,.2f}</td>
                        </tr>
                        <tr>
                            <td><b>Total Actual Expenses:</b></td>
                            <td style='text-align:right;'>RM {act:,.2f}</td>
                        </tr>
                        <tr>
                            <td><b>Difference (Est - Actual):</b></td>
                            <td style='text-align:right;'>RM {difference:,.2f}</td>
                        </tr>
                    </table>
                </div>
            """.format(est=total_est, act=total_act, difference=difference), unsafe_allow_html=True)

            # Add spacing before PDF button
            st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)

            # PDF Button
            offer_pdf_download(
                df_budget=df_preview,
                income=income,
                start_date=date.today().replace(day=1),
                end_date=date.today(),
                logo_path=LOGO_PATH
            )

        else:
            st.info("No budget items found yet. Use the categories above to build your plan.")

    except Exception as e:
        st.error(f"Unable to load budget preview: {e}")

    # ============================
    # Save Budget (confirmation)
    # ============================
    # Info to click to save budget
    st.info("CLICK ONCE to SAVE your budget plan. Then CLICK AGAIN to CONFIRM your budget plan")
    if st.button("💾 Save Budget Plan", use_container_width=True):
        # re-check totals at click
        income_now = get_income()
        total_now  = get_total_estimate()
        if total_now <= 0:
            st.warning("⚠️ No budget items found. Please add amounts above first.")
        elif total_now > income_now:
            st.session_state.save_status = "over_budget"
            st.session_state.over_amount = total_now - income_now
        else:
            # Mark confirmed = 1 for all current rows with positive estimate
            conn = get_conn()
            cur = conn.cursor()
            user_id = get_current_user_id(conn)

            cur.execute("""
                UPDATE money_magic_budget
                SET confirmed = 1,
                    last_updated = ?
                WHERE user_id = ?
                  AND estimated_amount IS NOT NULL
                  AND estimated_amount > 0;
            """, (_now(), user_id))

            conn.commit()
            conn.close()

            st.session_state.save_status = "ok"
            st.toast("✅ Budget confirmed successfully.", icon="✅")
            time.sleep(0.15)

    # Persistent feedback after Save attempts
    if st.session_state.get("save_status") == "over_budget":
        st.error(
            f"🚫 Your total planned budget exceeds your income "
            f"by RM {st.session_state.get('over_amount', 0):,.2f}. "
            "Please adjust and press Save again."
        )
    elif st.session_state.get("save_status") == "ok":
        st.success("✅ Budget saved and confirmed. You can download the PDF above if needed.")

    # Button to create a new budget
    if st.button("✏️Create New Budget Plan", use_container_width=True):
        clear_existing_budget()
        for key in ["budget", "categories", "budget_saved", "save_status", "over_amount"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    # RENEW BUDGET
    if st.button("🔁 Renew Budget", use_container_width=True):
        # Ensure user is logged in and fetch user_id
        user_id = get_current_user_id()

        if user_id is None:
            st.error("User not logged in! Please log in to continue.")
            return

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE money_magic_budget
            SET actual_amount = 0,
                envelope_balance = 0,
                payment_progress = 'Not Paid',
                status = 'Pending',
                last_updated = NULL
            WHERE user_id = ?;
            """,
            (user_id,),  # Pass user_id to the query
        )
        conn.commit()
        conn.close()
        st.success("Budget renewed successfully. All actual/envelope amounts reset.")
        time.sleep(0.5)
        st.rerun()

        new_start = date.today()
        new_end = new_start + timedelta(days=30)
        st.session_state["budget_start"] = new_start
        st.session_state["budget_end"] = new_end
        st.session_state.tracker_active = True
        st.session_state.tracker_start_dt = datetime.now()
        st.session_state.tracker_end_dt = datetime.combine(new_end, datetime.max.time())
        st.session_state.tracker_email_end = None
        st.session_state.tracker_expired_email_end = None
        st.session_state.summary_email_sent = None

        st.success("🎯 Budget renewed for another 30 days. All actual/envelope amounts reset.")
        time.sleep(0.5)
        st.rerun()
    # ============================
    # Navigation
    # ============================
    st.markdown("<hr style='border: 0.5px solid #181601; margin: 30px 0;'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🏠 Return to Main Menu", use_container_width=True):
            st.session_state.page = "main_menu"
            st.success("Returning to main menu...")
            time.sleep(0.2)
            st.rerun()
    with c2:
        if st.button("💼 Go to MoneyMap", use_container_width=True):
            st.session_state.page = "money_map"   # align with your router key
            st.success("Opening MoneyMap...")
            time.sleep(0.2)
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
