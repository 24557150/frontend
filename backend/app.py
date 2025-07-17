from flask import Flask, request, jsonify, g
import os
import sqlite3
from werkzeug.utils import secure_filename

# === 基本設定 ===
app = Flask(__name__)
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

# ✅ 第 1：上傳圖片 API（並寫入資料庫）
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
    path = os.path.join(save_dir, filename)
    image.save(path)

    # ➕ 寫入 wardrobe 資料表
    db = get_db()
    db.execute(
        "INSERT INTO wardrobe (user_id, filename, category) VALUES (?, ?, ?)",
        (user_id, filename, category)
    )
    db.commit()

    return jsonify({"status": "ok", "filename": filename})


# ✅ 第 2：取得使用者的圖片清單 API
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

    return jsonify([
        {"url": f"{base_url}/{row['category']}/{row['filename']}", "category": row['category']}
        for row in rows
    ])


# ✅ 測試用首頁
@app.route('/')
def index():
    return 'Server running. You can POST to /upload or GET /wardrobe'

if __name__ == '__main__':
    app.run(debug=True)
