import sqlite3

conn = sqlite3.connect("smartspend.db")
cur = conn.cursor()

print("=== USERS TABLE ===")
cur.execute("PRAGMA table_info(users);")
print(cur.fetchall())

print("\n=== MONEY MAGIC INCOME TABLE ===")
cur.execute("PRAGMA table_info(money_magic_income);")
print(cur.fetchall())

conn.close()
