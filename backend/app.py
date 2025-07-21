from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app, supports_credentials=True)  # 允許跨來源，支援 LINE WebView

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
DATABASE = os.path.join(BASE_DIR, "database", "db.sqlite")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === 資料庫連線 ===
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# === 上傳 API ===
@app.route('/upload', methods=['POST'])
def upload():
    image = request.files.get('image')
    category = request.form.get('category')
    user_id = request.form.get('user_id')

    if not image or not category or not user_id:
        return jsonify({"status": "error", "message": "缺少必要參數"}), 400

    save_dir = os.path.join(UPLOAD_FOLDER, user_id, category)
    os.makedirs(save_dir, exist_ok=True)

    filename = secure_filename(image.filename)
    filepath = os.path.join(save_dir, filename)
    image.save(filepath)

    # 儲存在 DB 的路徑，不重複加 static
    rel_path = f"/static/uploads/{user_id}/{category}/{filename}".replace("\\", "/")
    db = get_db()
    db.execute(
        "INSERT INTO wardrobe (user_id, filename, category) VALUES (?, ?, ?)",
        (user_id, filename, category)
    )
    db.commit()

    return jsonify({"status": "ok", "path": rel_path, "category": category})

# === 讀取衣櫃 API ===
@app.route('/wardrobe', methods=['GET'])
def wardrobe():
    user_id = request.args.get('user_id')
    category = request.args.get('category')

    if not user_id:
        return jsonify({"status": "error", "message": "缺少 user_id"}), 400

    db = get_db()
    query = "SELECT filename, category FROM wardrobe WHERE user_id = ?"
    params = [user_id]
    if category and category != 'all':
        query += " AND category = ?"
        params.append(category)

    rows = db.execute(query, params).fetchall()

    return jsonify({
        "images": [
            {
                "path": f"/static/uploads/{user_id}/{row['category']}/{row['filename']}".replace("\\", "/"),
                "category": row['category']
            } for row in rows
        ]
    })

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
        try:
            # paths 傳來的是 /static/uploads/...，去掉前綴
            if rel_path.startswith("/static/uploads/"):
                rel = rel_path[len("/static/uploads/"):]
                parts = rel.split("/", 2)  # user_id/category/filename
                if len(parts) == 3:
                    u_id, category, filename = parts
                    if u_id == user_id:
                        db.execute(
                            "DELETE FROM wardrobe WHERE user_id = ? AND category = ? AND filename = ?",
                            (user_id, category, filename)
                        )
                        file_path = os.path.join(UPLOAD_FOLDER, user_id, category, filename)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        deleted += 1
        except Exception as e:
            print("刪除錯誤:", e)

    db.commit()
    return jsonify({"status": "ok", "deleted": deleted})

# 測試用首頁
@app.route('/')
def index():
    return jsonify({"status": "running", "message": "Flask 伺服器運行中"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)  # 開放外部連線
