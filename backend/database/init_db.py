<<<<<<< HEAD
import sqlite3, os

# 專案根目錄
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 資料庫與 Schema 檔案路徑
DB_PATH = os.path.join(BASE_DIR, 'database', 'db.sqlite')
SCHEMA_PATH = os.path.join(BASE_DIR, 'database', 'schema.sql')

# 確保 database 資料夾存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 讀取 schema.sql 並建立資料庫
with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
    schema = f.read()

conn = sqlite3.connect(DB_PATH)
conn.executescript(schema)
conn.commit()
conn.close()

print(f"✅ SQLite 資料庫初始化完成，路徑: {DB_PATH}")

=======
import sqlite3, os

# 專案根目錄
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 資料庫與 Schema 檔案路徑
DB_PATH = os.path.join(BASE_DIR, 'database', 'db.sqlite')
SCHEMA_PATH = os.path.join(BASE_DIR, 'database', 'schema.sql')

# 確保 database 資料夾存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 讀取 schema.sql 並建立資料庫
with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
    schema = f.read()

conn = sqlite3.connect(DB_PATH)
conn.executescript(schema)
conn.commit()
conn.close()

print(f"✅ SQLite 資料庫初始化完成，路徑: {DB_PATH}")

>>>>>>> 2bbfa7a7c2328490db4598e217cfabed6bc0ed59
