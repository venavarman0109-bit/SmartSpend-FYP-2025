#Author : Sharvena A/P Kumaran
#Student ID : 0128131
#FYP PROJECT 2025 UNIVERSITY OF WOLLONGONG MALAYSIA
#Main Menu Page
import streamlit as st
import datetime
import os
import base64
import time

# ============================================================
#              CONSTANT PATHS (ADJUST IF NEEDED)
# ============================================================
BG_PATH = r"C:/Users/sharv/Downloads/UOW/FYP/FYP2/Malaysian-Ringgit.jpg"
LOGO_PATH = r"C:/Users/sharv/Downloads/UOW/FYP/FYP2/smartspend_logo.png"


# ============================================================
#              BACKGROUND IMAGE LOADER (CLEAN)
# ============================================================
def add_bg_from_local(image_file: str):
    """Set full-page background using a local image encoded in base64."""
    if not os.path.exists(image_file):
        return  # fail silently, just no background

    with open(image_file, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()

    # IMPORTANT: encoded is used ONLY inside CSS url() – never printed alone
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            background-repeat: no-repeat;
        }}

        .main {{
            background-color: rgba(255, 255, 255, 0.80);
            border-radius: 12px;
            padding: 15px;
        }}

        body {{ 
            overflow-y: scroll; 
        }}

        .card {{
            background: linear-gradient(to right, #ffffba, #baffc9, #bae1ff);
            color: #00008B;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            margin: 15px 0;
            box-shadow: 0px 5px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
            font-size: 22px;
            font-weight: 600;
        }}

        .card:hover {{
            transform: translateY(-6px);
            box-shadow: 0px 8px 18px rgba(0,0,0,0.25);
        }}

        div.stButton > button {{
            background: linear-gradient(to right, #ffffba, #baffc9, #bae1ff);
            color: #00008B;
            border: none;
            border-radius: 8px;
            padding: 0.6em 1.5em;
            font-weight: 800 !important;
            letter-spacing: 0.3px;
            font-size: 16px;
            cursor: pointer;
            transition: 0.3s ease;
        }}

        div.stButton > button:hover {{
            filter: brightness(1.1);
            transform: scale(1.03);
        }}

        .footer-note {{
            text-align: center;
            font-style: italic;
            color: #006400;
            font-size: 15px;
            margin-top: 50px;
        }}

        .stProgress > div > div > div > div {{
            background: linear-gradient(to right, #ffffba, #baffc9, #bae1ff);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
#                      MAIN MENU PAGE
# ============================================================
def main_menu():
    # --- BLOCK ACCESS IF USER NOT LOGGED IN ---
    if "user_id" not in st.session_state or st.session_state.get("user_id") is None:
        st.error("You must be logged in to access the SmartSpend Main Menu.")
        st.session_state.page = "login"
        st.rerun()
        return

    # Ensure username & email always exist
    username = st.session_state.get("username", "User")
    email = st.session_state.get("email", None)
    if not email:
        st.error("Session expired. Please log in again.")
        st.session_state.page = "login"
        st.rerun()
        return

    # Background
    add_bg_from_local(BG_PATH)
    today = datetime.datetime.now().strftime("%A, %d %B %Y")

    # ---------- HEADER ----------
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode()

        st.markdown(
            f"""
            <div style="
                display:flex;
                align-items:center;
                justify-content:center;
                gap:40px;
                background-color:rgba(5,75,112,0.88);
                border-radius:18px;
                padding:25px 45px;
                box-shadow:0 4px 15px rgba(0,0,0,0.1);
                margin-top:25px;
                margin-bottom:25px;
            ">
                <img src="data:image/png;base64,{logo_base64}"
                     style="
                        width:180px;
                        height:auto;
                        border-radius:50%;
                        box-shadow:0 4px 10px rgba(0,0,0,0.25);
                     ">
                <div style="text-align:left; white-space:nowrap;">
                    <h2 style="
                        color:#F5C827;
                        font-weight:800;
                        margin:0;
                        font-size:28px;
                        white-space:nowrap;
                    ">
                        👋 Welcome, {username}!
                    </h2>
                    <p style="
                        color:#0BD1F4;
                        font-style:italic;
                        margin:5px 0;
                        font-size:16px;
                    ">
                        {today}
                    </p>
                    <p style="
                        color:#F5C827;
                        font-weight:bold;
                        margin-top:5px;
                        font-size:15px;
                    ">
                        MoneyMagic: The magic of my intelligence,
                        is the logic of your finance
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            f"""
            <div style="text-align:center; margin-top:25px;">
                <h2 style="color:#003366; font-weight:800;">
                    👋 Welcome back, {username}!
                </h2>
                <p style="color:#008000; font-style:italic;">{today}</p>
                <p style="color:#f4ba09; font-weight:bold;">
                    MoneyMagic: The magic of my intelligence,
                    is the logic of your finance
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------- NAVIGATION ----------
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🎯 MoneyMagic - Smart Budget Planner", use_container_width=True):
        st.session_state.page = "money_magic"
        st.rerun()

    if st.button("🗺️ Money Map - My Money Tracker & Smart Wallet", use_container_width=True):
        st.session_state.page = "money_map"
        st.rerun()

    if st.button("🧠 MoneyTalks — AI Financial Advisor", use_container_width=True):
        st.session_state.page = "moneytalks"
        st.rerun()

    if st.button("📊 Money Map Tracker", use_container_width=True):
        st.session_state.page = "analysis"
        st.rerun()

    st.markdown("<hr style='border: 0.5px solid #181601; margin: 30px 0;'>", unsafe_allow_html=True)

    if st.button("👤 My SmartSpend Profile", use_container_width=True):
        st.session_state.page = "account_details"
        st.rerun()

    # ---------- LOGOUT (FULL CLEAR) ----------
    if st.button("🚪 Logout", use_container_width=True):
        for key in ["user_id", "email", "username", "page", "otp", "otp_purpose", "logged_in"]:
            if key in st.session_state:
                del st.session_state[key]
        st.success("👋 Logged out successfully!")
        st.session_state.page = "login"
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
