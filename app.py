from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os
import sqlite3
from werkzeug.utils import secure_filename
import requests  # 呼叫 Hugging Face API

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app, supports_credentials=True)

# 專案路徑設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
DATABASE = os.path.join(DB_DIR, "db.sqlite")
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Hugging Face BLIP API URL (換成你的 Space 名稱)
BLIP_API_URL = "https://yushon-blip-caption-service.hf.space/run/predict"

# 呼叫 Hugging Face Space 取得 caption
def get_caption(image_path):
    files = {'data': (os.path.basename(image_path), open(image_path, 'rb'), 'image/png')}
    try:
        response = requests.post(BLIP_API_URL, files=files, timeout=60)
        result = response.json()
        caption = result.get("data", [""])[0]  # Gradio Space 回傳格式
        return caption
    except Exception as e:
        print(f"BLIP API 調用錯誤: {e}")
        return ""

# 資料庫連線
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        # 確保 wardrobe 資料表存在，含 tags 欄位
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
            pass
        g.db.commit()
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db:
        db.close()

# 上傳圖片 API
@app.route('/upload', methods=['POST'])
def upload():
    image = request.files.get('image')
    category = request.form.get('category')
    user_id = request.form.get('user_id')

    if not image or not category or not user_id:
        return jsonify({"status": "error", "message": "缺少必要參數"}), 400

    # 先存圖片
    save_dir = os.path.join(UPLOAD_FOLDER, user_id, category)
    os.makedirs(save_dir, exist_ok=True)
    filename = secure_filename(image.filename)
    filepath = os.path.join(save_dir, filename)
    image.save(filepath)

    # 呼叫 Hugging Face BLIP API 生成 caption (當作 tags)
    tags = get_caption(filepath)

    # 存入 SQLite
    rel_path = f"/static/uploads/{user_id}/{category}/{filename}".replace("\\", "/")
    db = get_db()
    db.execute("INSERT INTO wardrobe (user_id, filename, category, tags) VALUES (?, ?, ?, ?)",
               (user_id, filename, category, tags))
    db.commit()

    return jsonify({"status": "ok", "path": rel_path, "category": category, "tags": tags})

# 讀取衣櫃 API
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
        {"path": f"/static/uploads/{user_id}/{row['category']}/{row['filename']}",
         "category": row['category'], "tags": row['tags'] or ''}
        for row in rows
    ]})

# 更新 tags API (如果要手動補 tags 用)
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

# 刪除圖片 API
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

# 測試首頁
@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Flask 伺服器運行中"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
