from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app, supports_credentials=True)  # 支援 GitHub Pages / LINE LIFF 跨網域

# === 設定目錄 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
DATABASE = os.path.join(DB_DIR, "db.sqlite")
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === 資料庫連線 ===
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        # 確保 wardrobe 資料表與 tags 欄位存在
        g.db.execute("""
        CREATE TABLE IF NOT EXISTS wardrobe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            category TEXT NOT NULL,
            tags TEXT
        )
        """)
        try:
            g.db.execute("ALTER TABLE wardrobe ADD COLUMN tags TEXT")
        except sqlite3.OperationalError:
            pass  # 欄位已存在
        g.db.commit()
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db:
        db.close()

# === 上傳 API ===
@app.route('/upload', methods=['POST'])
def upload():
    image = request.files.get('image')
    category = request.form.get('category')
    user_id = request.form.get('user_id')
    tags = request.form.get('tags', '')  # 可為空

    if not image or not category or not user_id:
        return jsonify({"status": "error", "message": "缺少必要參數"}), 400

    save_dir = os.path.join(UPLOAD_FOLDER, user_id, category)
    os.makedirs(save_dir, exist_ok=True)
    filename = secure_filename(image.filename)
    filepath = os.path.join(save_dir, filename)
    image.save(filepath)

    rel_path = f"/static/uploads/{user_id}/{category}/{filename}".replace("\\", "/")
    db = get_db()
    db.execute("INSERT INTO wardrobe (user_id, filename, category, tags) VALUES (?, ?, ?, ?)",
               (user_id, filename, category, tags))
    db.commit()

    return jsonify({"status": "ok", "path": rel_path, "category": category, "tags": tags})

# === 讀取衣櫃 API ===
@app.route('/wardrobe', methods=['GET'])
def wardrobe():
    user_id = request.args.get('user_id')
    category = request.args.get('category')
    if not user_id:
        return jsonify({"status": "error", "message": "缺少 user_id"}), 400

    db = get_db()
    query = "SELECT filename, category, tags FROM wardrobe WHERE user_id = ?"
    params = [user_id]
    if category and category != "all":
        query += " AND category = ?"
        params.append(category)

    rows = db.execute(query, params).fetchall()
    return jsonify({"images": [
        {
            "path": f"/static/uploads/{user_id}/{row['category']}/{row['filename']}",
            "category": row['category'],
            "tags": row['tags'] or ''
        } for row in rows
    ]})

# === 更新 tags API ===
@app.route('/update_tags', methods=['POST'])
def update_tags():
    data = request.get_json()
    user_id = data.get('user_id')
    filename = data.get('filename')
    category = data.get('category')
    tags = data.get('tags', '')

    if not user_id or not filename or not category:
        return jsonify({"status": "error", "message": "缺少參數"}), 400

    db = get_db()
    db.execute("UPDATE wardrobe SET tags = ? WHERE user_id = ? AND filename = ? AND category = ?",
               (tags, user_id, filename, category))
    db.commit()
    return jsonify({"status": "ok", "filename": filename, "tags": tags})

# === 刪除 API ===
@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    user_id = data.get('user_id')
    paths = data.get('paths', [])
    if not user_id or not paths:
        return jsonify({"status": "error", "message": "缺少 user_id 或 paths"}), 400

    db = get_db()
    deleted = 0
    for rel_path in paths:
        if rel_path.startswith("/static/uploads/"):
            rel = rel_path[len("/static/uploads/"):]
            parts = rel.split("/", 2)
            if len(parts) == 3:
                u_id, category, filename = parts
                if u_id == user_id:
                    db.execute("DELETE FROM wardrobe WHERE user_id=? AND category=? AND filename=?",
                               (user_id, category, filename))
                    file_path = os.path.join(UPLOAD_FOLDER, user_id, category, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    deleted += 1
    db.commit()
    return jsonify({"status": "ok", "deleted": deleted})

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Flask 伺服器運行中"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
