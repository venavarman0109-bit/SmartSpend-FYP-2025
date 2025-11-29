import streamlit as st
import os
import base64
import sqlite3
from datetime import datetime

from login_register import get_conn, send_email

# ============================================================
#   GLOBAL CONSTANTS (FOR FILE CLEANUP ON DELETE)
# ============================================================
STATEMENTS_DIR = r"C:\Users\sharv\Downloads\UOW\FYP\FYP2\monthly_statements"

st.markdown("""
<style>
.profile-card {
    background: rgba(255,255,255,0.78);
    padding: 25px 30px;
    border-radius: 18px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.18);
}

.profile-label-main {
    font-size: 1.1rem;
    font-weight: 700;
    color: #003366;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
#   BACKGROUND IMAGE LOADER
# ============================================================
def add_bg_from_local(image_file: str):
    try:
        with open(image_file, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()

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
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        # If background fails, do nothing and continue
        pass


# ============================================================
#   LOAD LOGGED-IN USER
# ============================================================
def _load_current_user():
    """
    Load current user details using the email stored in session_state.
    Uses the correct columns from the `users` table.
    """
    email = st.session_state.get("email", "")

    if not email:
        return {"name": "", "email": "", "contact": "", "created_at": ""}

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT profile_name, email, contact, created_at
        FROM users
        WHERE email = ?
    """, (email,))
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "name": row[0],
            "email": row[1],
            "contact": row[2],
            "created_at": row[3]
        }

    return {"name": "", "email": "", "contact": "", "created_at": ""}


# ============================================================
#   ACCOUNT DETAILS PAGE
# ============================================================
def account_details_page():
    # Set background
    add_bg_from_local(r"C:\Users\sharv\Downloads\UOW\FYP\FYP2\Account details bg.jpg")

    user = _load_current_user()
    original_email = user["email"]

    # Guard: if no user loaded, send back to login
    if not original_email:
        st.error("No active account found. Please log in again.")
        if st.button("Go to Login Page"):
            st.session_state.page = "login"
            st.rerun()
        return

    # ------------------------------------------------------------
    # PAGE TITLE
    # ------------------------------------------------------------
    st.markdown("""
        <h1 style='color:#003366; font-weight:900; text-align:left;
        margin-top:0px; margin-bottom:-5px;'>
            👤 Account Details
        </h1>
    """, unsafe_allow_html=True)

    st.markdown(
        "<p style='font-weight:700; font-style:italic; color:#008000;'>"
        "Manage your SmartSpend profile, contact and password securely."
        "</p>",
        unsafe_allow_html=True
    )

    # ------------------------------------------------------------
    # CONTAINER STYLES
    # ------------------------------------------------------------
    st.markdown("""
        <style>
            .acc-panel {
                background: rgba(255,255,255,0.85);
                padding: 35px;
                border-radius: 20px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.20);
                margin-top: 15px;
                width: 100%;
            }

            .section-title {
                font-size: 23px;
                font-weight: 800;
                color: #003366;
                margin-bottom: 8px;
            }

            .section-note {
                color: #555;
                font-size: 14px;
                margin-bottom: 18px;
            }

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

            .profile-wrapper {
                max-width: 700px;
                margin: 0 auto;
                background: rgba(255,255,255,0.82);
                padding: 35px 40px;
                border-radius: 20px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.18);
            }

            .profile-label {
                font-size: 30px;
                font-weight: 800;
                color: #003366;
                margin-bottom: 6px;
            }

            .stTextInput > div > div > input {
                background: rgba(252,243,187,0.95) !important;
                border: 2px solid #aac5ff !important;
                border-radius: 25px !important;
                padding: 15px !important;
                font-size: 25px !important;
                font-weight: 600 !important;
                color: #003366 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Convert ISO timestamp to readable date
    try:
        dt = datetime.fromisoformat(user["created_at"])
        clean_date = dt.strftime("%A, %d %B %Y")
    except Exception:
        clean_date = user["created_at"]

    st.markdown(f"**Member since:** {clean_date}")
    st.markdown("<hr style='border: 0.5px solid #181601; margin: 30px 0;'>", unsafe_allow_html=True)

    # ------------------------------------------------------------
    # PROFILE INFO
    # ------------------------------------------------------------

    # Profile Name
    st.markdown("<div class='profile-label'>Profile Name</div>", unsafe_allow_html=True)
    profile_name = st.text_input(
        "",
        value=user["name"],
        label_visibility="collapsed",
        key="profile_name_input"
    )

    # Contact Number
    st.markdown("<div class='profile-label' style='margin-top:18px;'>Contact Number</div>", unsafe_allow_html=True)
    contact = st.text_input(
        "",
        value=user["contact"],
        label_visibility="collapsed",
        key="contact_input"
    )

    # Email Address
    st.markdown("<div class='profile-label' style='margin-top:18px;'>Email Address</div>", unsafe_allow_html=True)
    email = st.text_input(
        "",
        value=user["email"],
        label_visibility="collapsed",
        key="email_input"
    )

    if st.button("💾 Save Profile Changes"):
        # Basic validation
        if not profile_name or not email or not contact:
            st.error("All fields are required.")
        else:
            try:
                conn = get_conn()
                cur = conn.cursor()

                # Check if new email is already used by another account
                if email != original_email:
                    cur.execute(
                        "SELECT id FROM users WHERE email = ?;",
                        (email,)
                    )
                    existing = cur.fetchone()
                    if existing:
                        conn.close()
                        st.error("This email is already registered to another account.")
                    else:
                        # Safe to update
                        cur.execute("""
                            UPDATE users
                            SET profile_name = ?, email = ?, contact = ?
                            WHERE email = ?
                        """, (profile_name, email, contact, original_email))
                        conn.commit()
                        conn.close()

                        # Update session state
                        st.session_state["username"] = profile_name
                        st.session_state["email"] = email

                        st.success("Profile updated successfully!")
                else:
                    # Email unchanged, only update name and contact
                    cur.execute("""
                        UPDATE users
                        SET profile_name = ?, contact = ?
                        WHERE email = ?
                    """, (profile_name, original_email, original_email))
                    conn.commit()
                    conn.close()

                    st.session_state["username"] = profile_name
                    st.session_state["email"] = original_email

                    st.success("Profile updated successfully!")

            except Exception as e:
                st.error(f"An error occurred while updating profile: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------------------------
    # CHANGE PASSWORD SECTION
    # ------------------------------------------------------------
    st.markdown("<hr style='border: 0.5px solid #181601; margin: 30px 0;'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🔐 Change Password</div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='margin-bottom:20px; font-weight:900; color:#127005;'>You will be redirected to the password reset page and Login again.</div>",
        unsafe_allow_html=True
    )
    if st.button("Go to Reset Password Page"):
        st.session_state.page = "reset_password"
        st.rerun()

    # ================================================
    #   DELETE ACCOUNT SECTION (FULL CLEANUP)
    # ================================================
    st.markdown("<hr style='border: 0.5px solid #181601; margin: 30px 0;'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>😵 Delete My Account</div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:20px; font-weight:900; color:#8B0000;'>⚠️ Danger Zone</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div style='margin-bottom:20px; font-weight:900; color:#9C2007;'>Deleting your SmartSpend account is permanent. "
        "All your expense history, budget plans and records will be permanently removed.</div>",
        unsafe_allow_html=True
    )

    # Persistent delete flag
    if "pending_delete" not in st.session_state:
        st.session_state.pending_delete = False

    delete_btn = st.button("🗑️ Delete My Account", key="delete_account_btn")

    if delete_btn:
        st.session_state.pending_delete = True
        st.rerun()

    if st.session_state.pending_delete:
        st.warning("Are you sure you want to permanently delete your account? This action cannot be undone.")

        col1, col2 = st.columns(2)
        confirm = col1.button("Yes, delete my account", key="confirm_delete")
        cancel = col2.button("Cancel", key="cancel_delete")

        if confirm:
            try:
                user_email = st.session_state.get("email")
                user_name = st.session_state.get("username", "SmartSpend user")

                conn = get_conn()
                cur = conn.cursor()

                # Look up user_id
                cur.execute("SELECT id FROM users WHERE email = ?;", (user_email,))
                row = cur.fetchone()
                user_id = row[0] if row else None

                if user_id is not None:
                    # Try to remove all user-related records
                    # Each block is protected so missing tables will not crash the app
                    candidate_tables = [
                        "money_magic_budget",
                        "smartspend_wallet",
                        "transactions",
                        "income_table",
                        "incomes",
                        "user_income"
                    ]

                    for table in candidate_tables:
                        try:
                            cur.execute(f"DELETE FROM {table} WHERE user_id = ?;", (user_id,))
                        except sqlite3.OperationalError:
                            # Table might not exist in this DB; safely ignore
                            pass

                    # Finally, delete user row
                    cur.execute("DELETE FROM users WHERE id = ?;", (user_id,))

                    conn.commit()
                    conn.close()

                    # Remove user-specific monthly statements
                    try:
                        if os.path.exists(STATEMENTS_DIR):
                            for fname in os.listdir(STATEMENTS_DIR):
                                if fname.endswith(".pdf") and f"_{user_id}_" in fname:
                                    fpath = os.path.join(STATEMENTS_DIR, fname)
                                    try:
                                        os.remove(fpath)
                                    except Exception:
                                        pass
                    except Exception:
                        # If file cleanup fails, ignore silently
                        pass

                else:
                    # If user_id not found, still attempt to delete by email
                    try:
                        cur.execute("DELETE FROM users WHERE email = ?;", (user_email,))
                        conn.commit()
                        conn.close()
                    except Exception:
                        pass

                # Send confirmation email
                if user_email:
                    try:
                        send_email(
                            user_email,
                            "SmartSpend Account Deletion Confirmation",
                            f"""
Hi {user_name},

Your SmartSpend account ({user_email}) has been permanently deleted,
including all budgets, transactions, wallet records and statements.

If you did NOT request this deletion, contact our support team immediately.

Regards,
SmartSpend – The Intelligence of Finance
                            """
                        )
                    except Exception:
                        # Email failure should not block deletion
                        pass

                # Clear session
                for key in ["username", "email", "logged_in", "user_id", "pending_delete"]:
                    if key in st.session_state:
                        del st.session_state[key]

                st.success("Your account and all related financial records have been deleted successfully.")
                st.session_state.page = "login"
                st.rerun()

            except Exception as e:
                st.error(f"Error deleting account: {e}")

        if cancel:
            st.session_state.pending_delete = False
            st.info("Account deletion cancelled.")
            st.rerun()

    # ------------------------------------------------------------
    # NAVIGATION BACK
    # ------------------------------------------------------------
    st.markdown("<hr style='border: 0.5px solid #181601; margin: 30px 0;'>", unsafe_allow_html=True)
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
