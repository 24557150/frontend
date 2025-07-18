# backend/database/init_db.py

import sqlite3, os

# 確保 database 資料夾存在
os.makedirs("backend/database", exist_ok=True)

# 連線到 SQLite
conn = sqlite3.connect("backend/database/db.sqlite")

# 建立 wardrobe 資料表
conn.execute("""
CREATE TABLE IF NOT EXISTS wardrobe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    category TEXT NOT NULL
)
""")

conn.commit()
conn.close()
print("✅ 已成功建立 wardrobe 資料表")
