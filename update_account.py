#Author : Sharvena A/P Kumaran
#Student ID : 0128131
#FYP PROJECT 2025 UNIVERSITY OF WOLLONGONG MALAYSIA
#Update Account
import sqlite3

def update_existing_account(email):
    # Connect to the SQLite database
    conn = sqlite3.connect('smartspend.db')
    cur = conn.cursor()

    # Update the user's PIN field to NULL (remove PIN)
    cur.execute("UPDATE users SET pin = NULL WHERE email = ?", (email,))
    conn.commit()

    print(f"PIN removed for the account with email: {email}")

    # Close the database connection
    conn.close()

# Replace with your existing email
existing_email = "venavarman0109@gmail.com"
update_existing_account(existing_email)
