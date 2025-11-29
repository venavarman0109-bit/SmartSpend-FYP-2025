#Author : Sharvena A/P Kumaran
#Student ID : 0128131
#FYP PROJECT 2025 UNIVERSITY OF WOLLONGONG MALAYSIA
#main.py
import streamlit as st
import base64
from login_register import (
    login_page,
    forgot_password_page,
    register_page,
    verify_otp_page,
    reset_password_page
)
from mainmenu_page import main_menu
from moneymap_page import my_money_map_page
from moneytalks_advisor_page import moneytalks_page
from money_magic_page_file import money_magic_page
from transaction_history_page import transaction_history_page
from analysis_page import analysis_page
from account_details_page import account_details_page

# ============================================================
#             STREAMLIT PAGE CONFIGURATION
# ============================================================

# Function to encode the image to base64
def image_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Encode the image
img_base64 = image_to_base64(r"C:\Users\sharv\Downloads\UOW\FYP\FYP2\smartspend_logo.png")

# Set the page configuration with the base64-encoded image
st.set_page_config(
    page_title="SmartSpend",
    page_icon=f"data:image/png;base64,{img_base64}"
)

# ============================================================
#             PAGE ROUTING LOGIC
# ============================================================
# Set default page to login
if "page" not in st.session_state:
    st.session_state.page = "login"

# Routing to appropriate function based on session state
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "forgot_password":
    forgot_password_page()
elif st.session_state.page == "register":
    register_page()
elif st.session_state.page == "verify_otp":
    verify_otp_page()
elif st.session_state.page == "reset_password":
    reset_password_page()
elif st.session_state.page == "main_menu":
    main_menu()
elif st.session_state.page == "money_map":
    my_money_map_page()
elif st.session_state.page == "moneytalks":
    moneytalks_page()
elif st.session_state.page == "money_magic":
    money_magic_page()
elif st.session_state.page == "transaction_history":
    transaction_history_page()
elif st.session_state.page == "analysis":
    analysis_page()
elif st.session_state.page == "account_details":
    account_details_page()
