import sqlite3
import os

DB_PATH = "smartspend.db"  # same file used in login_register.py

def table_exists(cur, name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return cur.fetchone() is not None

def add_user_id_if_missing(cur, table: str):
    cur.execute(f"PRAGMA table_info({table});")
    cols = {r[1] for r in cur.fetchall()}
    if "user_id" not in cols:
        print(f"Adding user_id to {table} ...")
        cur.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER;")

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found in this folder.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Ensure money_magic_income has user_id, then clear data
    if table_exists(cur, "money_magic_income"):
        add_user_id_if_missing(cur, "money_magic_income")
        print("Clearing all rows from money_magic_income ...")
        cur.execute("DELETE FROM money_magic_income;")
    else:
        print("Creating money_magic_income ...")
        cur.execute("""
            CREATE TABLE money_magic_income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monthly_income REAL DEFAULT 0,
                updated_at TEXT,
                user_id INTEGER
            );
        """)

    # 2. Ensure money_magic_budget has user_id, then clear data
    if table_exists(cur, "money_magic_budget"):
        add_user_id_if_missing(cur, "money_magic_budget")
        print("Clearing all rows from money_magic_budget ...")
        cur.execute("DELETE FROM money_magic_budget;")
    else:
        print("Creating money_magic_budget ...")
        cur.execute("""
            CREATE TABLE money_magic_budget (
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

    # 3. Drop and recreate smartspend_wallet as multi-user
    print("Dropping and recreating smartspend_wallet ...")
    cur.execute("DROP TABLE IF EXISTS smartspend_wallet;")
    cur.execute("""
        CREATE TABLE smartspend_wallet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_income REAL DEFAULT 0,
            total_budget REAL DEFAULT 0,
            spent REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            last_updated TEXT
        );
    """)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_wallet_user ON smartspend_wallet(user_id);")

    # 4. Drop and recreate transactions as multi-user
    print("Dropping and recreating transactions ...")
    cur.execute("DROP TABLE IF EXISTS transactions;")
    cur.execute("""
        CREATE TABLE transactions (
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
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tx_user_date ON transactions(user_id, date);")

    conn.commit()
    conn.close()
    print("✅ Migration complete. money_magic_* cleared, wallet & transactions reset with user_id.")

if __name__ == "__main__":
    main()
