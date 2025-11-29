# repair_income_table.py
import sqlite3

# Path to your existing database
db_path = r"C:/Users/sharv/Downloads/UOW/FYP/FYP2/smartspend.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("🔧 Repairing table 'money_magic_income'...")

# Rename the old table if it exists
try:
    cur.execute("ALTER TABLE money_magic_income RENAME TO money_magic_income_old;")
    print("✅ Renamed old table to money_magic_income_old")
except sqlite3.OperationalError:
    print("ℹ️ No existing table found (fresh creation will proceed).")

# Create the corrected version with 'id'
cur.execute("""
    CREATE TABLE IF NOT EXISTS money_magic_income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monthly_income REAL DEFAULT 0,
        updated_at TEXT
    );
""")
print("✅ Created new table with id, monthly_income, updated_at")

# Try migrating any old data
try:
    cur.execute("SELECT monthly_income FROM money_magic_income_old LIMIT 1;")
    row = cur.fetchone()
    if row:
        cur.execute(
            "INSERT INTO money_magic_income (monthly_income, updated_at) VALUES (?, datetime('now'));",
            (row[0],)
        )
        print(f"✅ Migrated old income record (RM {row[0]:,.2f})")
except Exception as e:
    print(f"⚠️ No old data migrated: {e}")

# Drop the old table if it exists
cur.execute("DROP TABLE IF EXISTS money_magic_income_old;")
conn.commit()
conn.close()

print("🎉 Repair complete! You can now restart Streamlit.")
