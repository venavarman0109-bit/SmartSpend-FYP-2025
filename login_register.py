#Author : Sharvena A/P Kumaran
#Student ID : 0128131
#FYP PROJECT 2025 UNIVERSITY OF WOLLONGONG MALAYSIA
#Login-Register Page
import streamlit as st
import sqlite3
import os
import hashlib
import random
import time
import base64
import smtplib, ssl, socket
from email.message import EmailMessage
from datetime import datetime

from repair_db_columns import DB_PATH

# ---------- EMAIL CONFIG ----------
EMAIL_USER = "smartspend0109@gmail.com"
EMAIL_PASS = "fpst tgxx ilyh mrdn"


# ---------- DATABASE SETUP ----------
def get_conn():
    # Use the shared DB_PATH so everything points to the same database
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            contact TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """
    )
    conn.commit()
    conn.close()


# ---------- PASSWORD HASHING ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed_password):
    return hash_password(password) == hashed_password


# ---------- EMAIL FUNCTION ----------
def send_email(to, subject, body):
    original_getaddrinfo = socket.getaddrinfo  # keep original

    try:
        msg = EmailMessage()
        msg["From"] = EMAIL_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        context = ssl.create_default_context()

        def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
            return original_getaddrinfo(
                host, port, socket.AF_INET, type, proto, flags
            )

        socket.getaddrinfo = getaddrinfo_ipv4

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        return True

    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

    finally:
        # restore original resolver
        socket.getaddrinfo = original_getaddrinfo


# ---------- BACKGROUND ----------
def add_bg_from_local(image_file):
    if not os.path.exists(image_file):
        return
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
    """,
        unsafe_allow_html=True,
    )


# ---------- HEADER ----------
def display_header():
    add_bg_from_local("C:/Users/sharv/Downloads/UOW/FYP/FYP2/Login register bg.jpg")

    st.markdown(
        """
        <style>
            .header-container {
                display: flex; 
                flex-direction: column;
                align-items: center; 
                justify-content: center;
                gap: 10px;
                padding: 20px;
                text-align: center;
            }
            .header-title {
                font-size: 40px; 
                color:#003366; 
                font-weight:700;
            }
            .header-caption {
                color:#008000;
                font-style: italic;
                font-size: 18px;
            }

            /* Button styles */
            div.stButton > button {
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
            }
            div.stButton > button:hover {
                filter: brightness(1.1);
                transform: scale(1.03);
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='header-container'>", unsafe_allow_html=True)

    logo_path = "C:/Users/sharv/Downloads/UOW/FYP/FYP2/smartspend_logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)

    st.markdown(
        """
        <div class='header-title'>SmartSpend</div>
        <div class='header-caption'>The Intelligence of Finance</div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("</div><hr>", unsafe_allow_html=True)

# ============================================================
#   GLOBAL INPUT DESIGN — applies to Login, Register, OTP, Reset
# ============================================================
def apply_global_input_style():
    st.markdown("""
    <style>
    .profile-label {
        font-size: 30px;
        font-weight: 800;
        color: #003366;
        margin-bottom: 0px;
    }

    /* ---- UNIVERSAL INPUT BOX WRAPPER ---- */
    div[data-testid="stTextInput"] {
        background: transparent !important;
    }

    /* Outer frame */
    div[data-testid="stTextInput"] > div {
        background: rgba(5, 87, 112, 0.75) !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 40px !important;
        padding: 6px 16px !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Inner container */
    div[data-testid="stTextInput"] > div > div:nth-child(1) {
        background: transparent !important;
        border-radius: 40px !important;
        width: 100% !important;
    }

    /* Text field */
    div[data-testid="stTextInput"] input {
        background: solid !important;
        font-size: 25px !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
        padding-left: 6px !important;
        height: 35px !important;
    }

    /* Placeholder */
    div[data-testid="stTextInput"] input::placeholder {
        color: #FFFFFF !important;
        opacity: 0.7 !important;
    }

    /* Eye icon */
    div[data-testid="stTextInput"] svg {
        fill: #FFFFFF !important;
        width: 26px !important;
        height: 26px !important;
        margin-right: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
#                     LOGIN PAGE
# ============================================================

def login_page():
    apply_global_input_style()
    init_db()
    display_header()

    st.markdown("""
    <h2 style="
        color:#003366;
        font-weight:900;
        font-size:40px;
        margin-top:0px;
        margin-bottom:20px;
        display:flex;
        align-items:center;
        gap:12px;
    ">
        🔐 Login
    </h2>
    """, unsafe_allow_html=True)

    st.markdown("<div class='profile-label'>Email</div>", unsafe_allow_html=True)
    input_email = st.text_input("")

    st.markdown("<div class='profile-label'>Password</div>", unsafe_allow_html=True)
    password = st.text_input("", type="password")

    if st.button("Login"):
        email = (input_email or "").strip().lower()

        if not email or not password:
            st.warning("Please fill in both fields.")
            return

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if not user:
            st.error("Account not found.")
            return

        # user schema: id, profile_name, email, password, contact, created_at
        if not verify_password(password, user[3]):
            st.error("Incorrect password.")
            return

        # Store details BEFORE OTP
        st.session_state.email = user[2]
        st.session_state.username = user[1]
        st.session_state.otp_purpose = "login"

        otp = str(random.randint(100000, 999999))
        st.session_state.otp = otp

        body = (
            f"Hello {user[1]},\n\n"
            f"Your SmartSpend login verification code is:\n\n"
            f"{otp}\n\n"
            f"Do not share this code with anyone."
        )

        if send_email(email, "SmartSpend Login OTP", body):
            st.success("OTP sent to your email.")
            st.session_state.page = "verify_otp"
            st.rerun()
        else:
            st.error("Failed to send OTP.")

    # Forgot password
    if st.button("Forgot Password?"):
        st.session_state.page = "forgot_password"
        st.rerun()

    if st.button("Create Account"):
        st.session_state.page = "register"
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


# ============================================================
#                     FORGOT PASSWORD
# ============================================================

def forgot_password_page():
    apply_global_input_style()
    display_header()

    st.markdown("""
        <h2 style="
            color:#003366;
            font-weight:900;
            font-size:40px;
            margin-top:0px;
            margin-bottom:20px;
            display:flex;
            align-items:center;
            gap:12px;
        ">
            🤔 Forgot Password
        </h2>
        """, unsafe_allow_html=True)

    st.markdown("<div class='profile-label'>Email</div>", unsafe_allow_html=True)
    input_email = st.text_input("", key="login_email")

    if st.button("Send OTP"):
        email = (input_email or "").strip().lower()

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if not user:
            st.error("This email is not registered.")
            return

        st.session_state.email = email
        st.session_state.username = user[1]
        st.session_state.otp_purpose = "reset"

        otp = str(random.randint(100000, 999999))
        st.session_state.otp = otp

        body = (
            f"Hello {user[1]},\n\n"
            f"Your password reset verification code is:\n\n"
            f"{otp}\n\n"
            f"Do not share this code with anyone."
        )

        if send_email(email, "SmartSpend Password Reset OTP", body):
            st.success("OTP sent.")
            st.session_state.page = "verify_otp"
            st.rerun()
        else:
            st.error("Unable to send OTP.")

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


# ============================================================
#                     VERIFY OTP
# ============================================================

def verify_otp_page():
    apply_global_input_style()
    display_header()

    st.markdown(
        """<h2 style="color:#003366; font-weight:900; font-size:40px; margin-top:0px; margin-bottom:20px; display:flex; align-items:center; gap:12px;">🔐 Verify OTP</h2>""",
        unsafe_allow_html=True)

    otp_input = st.text_input("Enter OTP", type="password")

    if st.button("Verify"):
        stored_otp = st.session_state.get("otp")  # Get the OTP from session state
        purpose = st.session_state.get("otp_purpose")  # Get OTP purpose from session state

        # Check if the stored OTP exists and matches the input OTP
        if not stored_otp or otp_input != stored_otp:
            st.error("Incorrect OTP.")
            return

        # Clear OTP now that it's used
        st.session_state.otp = ""  # Clear the OTP after verification

        # Proceed with action based on OTP purpose
        if purpose == "login":
            email = getattr(st.session_state, "email", None)
            if email:
                with get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM users WHERE email = ?;", (email,))
                    row = cur.fetchone()
                    if row:
                        st.session_state.user_id = row[0]  # Store user ID in session state
                        st.session_state.logged_in = True  # Mark the user as logged in
                        st.session_state.page = "main_menu"  # Navigate to the main menu
                        st.rerun()  # Refresh to apply the page change
                    else:
                        st.error("No user found with the provided email.")
            else:
                st.error("No email found in session state.")

        elif purpose == "reset":
            # If OTP is for password reset, proceed to the reset password page
            st.session_state.otp_purpose = "reset_verified"  # Mark the reset OTP as verified
            st.session_state.page = "reset_password"  # Navigate to the reset password page
            st.rerun()  # Refresh to apply the page change

        else:
            st.error("Unknown OTP purpose.")  # In case there's no valid purpose in session state

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


# ============================================================
#                     RESET PASSWORD
# ============================================================

def reset_password_page():
    apply_global_input_style()
    display_header()

    st.markdown("""
               <h2 style="
                   color:#003366;
                   font-weight:900;
                   font-size:40px;
                   margin-top:0px;
                   margin-bottom:20px;
                   display:flex;
                   align-items:center;
                   gap:12px;
               ">
                   🔑 Reset Password
               </h2>
               """, unsafe_allow_html=True)

    # Ensure OTP was verified for reset
    if st.session_state.get("otp_purpose") not in ("reset_verified",):
        st.error("Please verify your OTP first.")
        if st.button("Back to Login"):
            st.session_state.page = "login"
            st.rerun()
        return

    st.markdown("<div class='profile-label'>New Password</div>", unsafe_allow_html=True)
    new_pw = st.text_input("", type="password")
    st.markdown("<div class='profile-label'>Confirm Password</div>", unsafe_allow_html=True)
    confirm_pw = st.text_input("", type="password")

    if st.button("Reset"):
        if new_pw != confirm_pw:
            st.error("Passwords do not match.")
            return

        hashed = hash_password(new_pw)
        email = (st.session_state.get("email") or "").strip().lower()

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
        conn.commit()
        conn.close()

        st.success("Password reset successfully!")
        # Clear reset state
        st.session_state.otp_purpose = None
        st.session_state.otp = ""
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


# ============================================================
#                       REGISTER
# ============================================================

def register_page():
    apply_global_input_style()
    init_db()
    display_header()

    st.markdown("""
                  <h2 style="
                      color:#003366;
                      font-weight:900;
                      font-size:40px;
                      margin-top:0px;
                      margin-bottom:20px;
                      display:flex;
                      align-items:center;
                      gap:12px;
                  ">
                      SignUp for SmartSpend Today !
                  </h2>
                  """, unsafe_allow_html=True)

    st.markdown("<div class='profile-label'>Profile Name</div>", unsafe_allow_html=True)
    profile_raw = st.text_input("", key="profile_name_input")
    st.markdown("<div class='profile-label'>Email</div>", unsafe_allow_html=True)
    email_raw = st.text_input("", key="email_input")
    st.markdown("<div class='profile-label'>Create Password</div>", unsafe_allow_html=True)
    pw = st.text_input("", type="password", key="password_input")
    st.markdown("<div class='profile-label'>Confirm Password</div>", unsafe_allow_html=True)
    cpw = st.text_input("", type="password", key="confirm_input")
    st.markdown("<div class='profile-label'>Contact Number</div>", unsafe_allow_html=True)
    contact_raw = st.text_input("", key="contact_input")

    if st.button("Register"):
        profile = (profile_raw or "").strip()
        email = (email_raw or "").strip().lower()
        contact = (contact_raw or "").strip()

        if not all([profile, email, pw, cpw, contact]):
            st.warning("All fields are required.")
            return
        if pw != cpw:
            st.error("Passwords do not match.")
            return

        hashed_pw = hash_password(pw)

        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO users (profile_name, email, password, contact, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (profile, email, hashed_pw, contact, datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()

            send_email(
                email,
                "Welcome to SmartSpend",
                f"Hello {profile},\n\nYour SmartSpend account has been created successfully!",
            )

            st.success("Account created!")
            st.session_state.page = "login"
            st.rerun()

        except sqlite3.IntegrityError:
            st.error("Email already registered.")

    if st.button("Back to Login"):
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
