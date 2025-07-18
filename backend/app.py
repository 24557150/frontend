from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os
import sqlite3
from werkzeug.utils import secure_filename

# === 初始化 Flask 與 CORS ===
app = Flask(__name__)
CORS(app)  # ✅ 支援跨來源請求，讓 GitHub Pages 可訪問

# === 設定資料夾與資料庫位置 ===
UPLOAD_FOLDER = os.path.join("static", "uploads")
DATABASE = os.path.join("database", "db.sqlite")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === 資料庫連線處理 ===
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

# ✅ 第 1：上傳圖片 API
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

    # ➕ 寫入資料庫
    db = get_db()
    db.execute(
        "INSERT INTO wardrobe (user_id, filename, category) VALUES (?, ?, ?)",
        (user_id, filename, category)
    )
    db.commit()

    return jsonify({"status": "ok", "filename": filename})

# ✅ 第 2：取得衣櫃圖片清單 API
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
    base_url = f"/static/uploads/{user_id}"

    return jsonify({
        "images": [
            {
                "path": os.path.join(base_url, row['category'], row['filename']).replace("\\", "/"),
                "category": row['category']
            } for row in rows
        ]
    })

# ✅ 第 3：刪除圖片 API
@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    user_id = data.get('user_id')
    paths = data.get('paths', [])

    if not user_id or not paths:
        return jsonify({"status": "error", "message": "缺少 user_id 或 paths"}), 400

    db = get_db()
    deleted = 0

    for full_path in paths:
        try:
            rel_path = full_path.split("/static/uploads/")[-1]
            category, filename = rel_path.replace(f"{user_id}/", "").split("/", 1)
            db.execute(
                "DELETE FROM wardrobe WHERE user_id = ? AND category = ? AND filename = ?",
                (user_id, category, filename)
            )
            file_path = os.path.join("static", "uploads", user_id, category, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            deleted += 1
        except Exception as e:
            print("刪除失敗:", e)

    db.commit()
    return jsonify({"status": "ok", "deleted": deleted})

# 測試用首頁
@app.route('/')
def index():
    return '✅ Flask 伺服器已啟動，可使用 /upload /wardrobe /delete'

if __name__ == '__main__':
    app.run(debug=True)
