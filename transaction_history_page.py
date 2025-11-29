#Author : Sharvena A/P Kumaran
#Student ID : 0128131
#FYP PROJECT 2025 UNIVERSITY OF WOLLONGONG MALAYSIA
#Transaction Hsitory Page
# ======================================================
# transaction_history_page.py (Updated – user-aware)
# ======================================================
import os
import base64
import calendar
from datetime import datetime

import pandas as pd
import streamlit as st

from fpdf import FPDF
from money_magic_page_file import get_conn, get_current_user_id

BG_PATH = r"C:\Users\sharv\Downloads\UOW\FYP\FYP2\Transaction history bg.jpg"
SAVE_DIR = r"C:\Users\sharv\Downloads\UOW\FYP\FYP2\monthly_statements"

# ======================================================
# BACKGROUND
# ======================================================
def _encode_local_image_to_base64(path: str):
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
            .pill {{
                display:inline-block;
                padding:6px 10px;
                border-radius:999px;
                border:1px solid #e6eef9;
                background:#f7fbff;
                color:#003366;
                margin-right:8px;
            }}
            div.stButton>button {{
                background: linear-gradient(to right,#ffffba,#baffc9,#bae1ff);
                color:#003366;
                border:none;
                border-radius:8px;
                padding:0.6em 1.2em;
                font-weight:700;
                cursor:pointer;
                transition:0.25s ease;
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


# ======================================================
# DATABASE HELPER
# ======================================================
def fetch_transactions() -> pd.DataFrame:
    """
    Fetch all transactions for the CURRENT USER only.
    Adds Flow and Signed amount columns for analysis and PDF.
    """
    conn = get_conn()
    user_id = get_current_user_id(conn)
    if user_id is None:
        conn.close()
        return pd.DataFrame()

    df = pd.read_sql_query(
        """
        SELECT 
            date AS 'Date',
            type AS 'Transaction Type',
            method AS 'Method',
            category AS 'Category',
            item AS 'Item',
            amount AS 'Amount (RM)',
            source AS 'From',
            target AS 'To',
            remarks AS 'Remarks',
            id
        FROM transactions
        WHERE user_id = ?
        ORDER BY datetime(date) DESC, id DESC;
        """,
        conn,
        params=(user_id,),
    )
    conn.close()

    if df.empty:
        return df

    # Normalise date & amount
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    df["_AmountNumeric"] = pd.to_numeric(
        df["Amount (RM)"], errors="coerce"
    ).fillna(0.0)

    # Classify direction of money
    def _direction(row):
        t = (row.get("Transaction Type") or "").strip().lower()
        m = (row.get("Method") or "").strip().lower()
        if t == "top up":
            return "IN"
        if t in ("payment", "withdrawal", "withdrawal (exceeded)", "payment (exceeded)"):
            return "OUT"
        if m == "refund":
            return "IN"
        return "INTERNAL"

    df["Flow"] = df.apply(_direction, axis=1)
    df["_Signed"] = df.apply(
        lambda r: r["_AmountNumeric"]
        if r["Flow"] == "IN"
        else (-r["_AmountNumeric"] if r["Flow"] == "OUT" else 0.0),
        axis=1,
    )

    df["Amount (RM)"] = df["_AmountNumeric"].map(lambda x: f"{x:,.2f}")
    df = df.drop(columns=["id"])
    return df


# ======================================================
# PDF EXPORT
# ======================================================
def export_to_pdf(df: pd.DataFrame) -> str:
    """
    Export a user-specific set of transactions to a landscape A4 PDF
    with totals and signed flows.
    """
    ORG_NAME = "SmartSpend – UOW Malaysia"

    class StyledPDF(FPDF):
        def header(self):
            logo_path = r"C:\Users\sharv\Downloads\UOW\FYP\FYP2\smartspend_logo.png"
            if os.path.exists(logo_path):
                self.image(logo_path, x=130, y=8, w=25)
            self.set_font("NotoSansVar", "", 16)
            self.ln(25)
            self.cell(0, 10, "SmartSpend Financial Statement", ln=1, align="C")
            self.set_font("NotoSansVar", "", 10)
            self.cell(0, 6, ORG_NAME, ln=1, align="C")
            self.cell(
                0,
                6,
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ln=1,
                align="C",
            )
            self.ln(5)
            self.set_draw_color(0, 51, 102)
            self.set_line_width(0.8)
            self.line(10, self.get_y(), 287, self.get_y())
            self.ln(6)

        def footer(self):
            self.set_y(-15)
            self.set_font("NotoSansVar", "", 9)
            self.set_text_color(130, 130, 130)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

        def add_watermark(self, text="SMARTSPEND"):
            self.set_text_color(220, 220, 220)
            self.set_font("NotoSansVar", "", 40)
            try:
                # If rotation context is available
                with self.rotation(45, x=self.w / 2, y=self.h / 2):
                    self.text(self.w / 4, self.h / 2, text)
            except Exception:
                # For older fpdf versions without rotation context manager
                pass
            self.set_text_color(0, 0, 0)

    pdf = StyledPDF(orientation="L", unit="mm", format="A4")
    # Font registration
    try:
        pdf.add_font(
            "NotoSansVar",
            "",
            r"C:\Users\sharv\Downloads\UOW\FYP\FYP2\NotoSans-VariableFont_wdth,wght.ttf",
            uni=True,
        )
    except Exception:
        # Fallback to core font
        pdf.set_font("Arial", "", 10)

    pdf.add_page()
    try:
        pdf.set_font("NotoSansVar", "", 10)
    except RuntimeError:
        pdf.set_font("Arial", "", 10)

    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_watermark("SMARTSPEND")

    # Ensure numeric helpers exist
    if "_AmountNumeric" not in df.columns or "_Signed" not in df.columns:
        df["_AmountNumeric"] = pd.to_numeric(
            df["Amount (RM)"].astype(str).str.replace(",", ""), errors="coerce"
        ).fillna(0.0)
        if "Flow" not in df.columns:
            def _direction(row):
                t = (str(row.get("Transaction Type")) or "").strip().lower()
                m = (str(row.get("Method")) or "").strip().lower()
                if t == "top up":
                    return "IN"
                if t in ("payment", "withdrawal", "withdrawal (exceeded)", "payment (exceeded)"):
                    return "OUT"
                if m == "refund":
                    return "IN"
                return "INTERNAL"

            df["Flow"] = df.apply(_direction, axis=1)

        df["_Signed"] = df.apply(
            lambda r: r["_AmountNumeric"]
            if r["Flow"] == "IN"
            else (-r["_AmountNumeric"] if r["Flow"] == "OUT" else 0.0),
            axis=1,
        )

    money_in = float(df.loc[df["Flow"] == "IN", "_AmountNumeric"].sum())
    money_out = float(df.loc[df["Flow"] == "OUT", "_AmountNumeric"].sum())
    net_flow = float(df["_Signed"].sum())

    # Columns for PDF
    pdf_df = df.copy()
    pdf_df = pdf_df[
        [
            "Date",
            "Transaction Type",
            "Method",
            "Category",
            "Item",
            "Flow",
            "Amount (RM)",
            "Remarks",
        ]
    ].copy()

    if "Signed Flow (RM)" not in pdf_df.columns:
        pdf_df.insert(
            pdf_df.columns.get_loc("Amount (RM)") + 1,
            "Signed Flow (RM)",
            df["_Signed"].map(lambda x: f"{x:,.2f}"),
        )

    cols = pdf_df.columns.tolist()
    base_w = 275
    weights = [
        2.2
        if c in ["Date", "Remarks"]
        else 1.8
        if c in ["Category", "Item"]
        else 1.3
        for c in cols
    ]
    widths = [base_w * (w / sum(weights)) for w in weights]

    # Header row
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    try:
        pdf.set_font("NotoSansVar", "", 9)
    except RuntimeError:
        pdf.set_font("Arial", "", 9)

    for w, c in zip(widths, cols):
        pdf.cell(w, 9, c, border=1, align="C", fill=True)
    pdf.ln(9)

    # Data rows
    for i, (_, row) in enumerate(pdf_df.iterrows()):
        if i % 2 == 0:
            pdf.set_fill_color(255, 255, 255)
        else:
            pdf.set_fill_color(242, 247, 255)
        pdf.set_text_color(0, 0, 0)

        for w, c in zip(widths, cols):
            text = "" if pd.isna(row[c]) else str(row[c])
            if len(text) > 60:
                text = text[:57] + "..."
            align = "R" if ("Amount" in c or "Flow (RM)" in c) else (
                "C" if c == "Flow" else "L"
            )
            pdf.cell(w, 7, text, border=1, align=align, fill=True)
        pdf.ln(7)

    # Summary
    pdf.ln(6)
    try:
        pdf.set_font("NotoSansVar", "", 11)
    except RuntimeError:
        pdf.set_font("Arial", "", 11)

    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 7, f"Money In: RM {money_in:,.2f}", ln=1, align="R")
    pdf.cell(0, 7, f"Money Out: RM {money_out:,.2f}", ln=1, align="R")
    if net_flow >= 0:
        pdf.set_text_color(0, 128, 0)
    else:
        pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 9, f"Net Cash Flow: RM {net_flow:,.2f}", ln=1, align="R")

    filename = f"SmartSpend_Financial_Statement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename


# ======================================================
# PAGE CONTENT
# ======================================================
def transaction_history_page():
    apply_bg()
    st.markdown(
        "<h2 style='color:#003366; text-align:center;'>📜 Transaction History</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    # Ensure user is logged in
    conn = get_conn()
    user_id = get_current_user_id(conn)
    conn.close()
    if user_id is None:
        st.error("You must be logged in to view your transaction history.")
        return

    # --- Ensure statement directory exists ---
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    # --- Auto generate previous month if missing (user-specific) ---
    today = datetime.today()
    year, month = today.year, today.month
    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1

    fname = f"SmartSpend_Statement_{user_id}_{year}_{month:02d}.pdf"
    path = os.path.join(SAVE_DIR, fname)

    if not os.path.exists(path):
        conn = get_conn()
        # Get current user again (just in case)
        user_check = get_current_user_id(conn)
        if user_check is None:
            conn.close()
            st.error("User session not found. Please log in again.")
            return

        first_day = datetime(year, month, 1)
        last_day = datetime(year, month, calendar.monthrange(year, month)[1])

        df_month = pd.read_sql_query(
            """
            SELECT 
                date AS 'Date',
                type AS 'Transaction Type',
                method AS 'Method',
                category AS 'Category',
                item AS 'Item',
                amount AS 'Amount (RM)',
                source AS 'From',
                target AS 'To',
                remarks AS 'Remarks'
            FROM transactions
            WHERE user_id = ?
              AND date(date) BETWEEN ? AND ?
            ORDER BY datetime(date);
            """,
            conn,
            params=(
                user_check,
                first_day.strftime("%Y-%m-%d"),
                last_day.strftime("%Y-%m-%d"),
            ),
        )
        conn.close()

        if not df_month.empty:
            pdf_file = export_to_pdf(df_month)
            os.replace(pdf_file, path)

    # --- List user-specific statement files (limit 24) ---
    files = sorted(
        [
            f
            for f in os.listdir(SAVE_DIR)
            if f.endswith(".pdf") and f"_{user_id}_" in f
        ],
        reverse=True,
    )

    if len(files) > 24:
        # Keep latest 24, delete older
        for f in files[24:]:
            try:
                os.remove(os.path.join(SAVE_DIR, f))
            except Exception:
                pass
        files = files[:24]

    # --- Fetch and display transactions ---
    df_all = fetch_transactions()
    if df_all.empty:
        st.warning("No transactions recorded yet.")
        # Navigation buttons still useful
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💰 Return to Money Map", use_container_width=True):
                st.session_state.page = "money_map"
                st.rerun()
        with c2:
            if st.button("🏠 Return to Main Menu", use_container_width=True):
                st.session_state.page = "main_menu"
                st.rerun()
        return

    st.markdown(
        "<h4 style='color:#003366;'>💼 Recorded Transactions</h4>",
        unsafe_allow_html=True,
    )

    money_in = float(df_all.loc[df_all["Flow"] == "IN", "_AmountNumeric"].sum())
    money_out = float(df_all.loc[df_all["Flow"] == "OUT", "_AmountNumeric"].sum())
    net_flow = float(df_all["_Signed"].sum())

    st.markdown(
        f"<span class='pill'>Deposited: RM {money_in:,.2f}</span>"
        f"<span class='pill'>Spent: RM {money_out:,.2f}</span>"
        f"<span class='pill'>Net: RM {net_flow:,.2f}</span>",
        unsafe_allow_html=True,
    )

    st.dataframe(df_all, use_container_width=True, height=480)

    # --- Monthly statements list ---
    st.markdown(
        "<h4 style='color:#003366;'>📆 Monthly Statements (Last 24 Months)</h4>",
        unsafe_allow_html=True,
    )
    if files:
        latest_file = files[0]
        for f in files:
            filepath = os.path.join(SAVE_DIR, f)
            try:
                tail = (
                    f.replace("SmartSpend_Statement_", "")
                    .replace(".pdf", "")
                )
                uid_str, y, m = tail.split("_")
                month_name = calendar.month_name[int(m)]
            except Exception:
                y, month_name = "----", "Unknown"

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                if f == latest_file:
                    st.markdown(
                        f"📄 **{month_name} {y} Statement** "
                        f"<span style='color:green;'>🟢 New</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.write(f"📄 **{month_name} {y} Statement**")
            with col2:
                # Local view link (works on your machine)
                st.markdown(f"[🔍 View](file:///{filepath})")
            with col3:
                with open(filepath, "rb") as f_obj:
                    st.download_button(
                        "⬇️ Download",
                        f_obj.read(),
                        file_name=f,
                        mime="application/pdf",
                        key=f"dl_{f}",
                    )
    else:
        st.info(
            "No monthly statements available yet. Generate one to start building your archive."
        )

    # --- Navigation ---
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💰 Return to Money Map", use_container_width=True):
            st.session_state.page = "money_map"
            st.rerun()
    with c2:
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
