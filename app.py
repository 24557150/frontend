from flask import Flask, request, jsonify, g
import os, sqlite3, io, datetime
from huggingface_hub import InferenceClient
from PIL import Image

app = Flask(__name__)
DB_PATH = "wardrobe.db"

HF_TOKEN = os.environ.get("HF_TOKEN")
client = InferenceClient(api_key=HF_TOKEN)

# --- SQLite 資料庫 ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("""
            CREATE TABLE IF NOT EXISTS wardrobe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                filename TEXT,
                category TEXT,
                mask_base64 TEXT,
                created_at TEXT
            )
        """)
        g.db.commit()
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db:
        db.close()

@app.route('/upload', methods=['POST'])
def upload():
    image = request.files.get('image')
    category = request.form.get('category')
    user_id = request.form.get('user_id')
    if not image or not category or not user_id:
        return jsonify({"status": "error", "message": "缺少必要參數"}), 400

    # 圖片 SegFormer 分割
    img = Image.open(image.stream).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    output = client.image_segmentation(buf, model="matei-dorian/segformer-b5-finetuned-human-parsing")

    mask_base64 = output["mask"]
    now = datetime.datetime.now().isoformat()

    # 儲存到 SQLite
    db = get_db()
    db.execute(
        "INSERT INTO wardrobe (user_id, filename, category, mask_base64, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, image.filename, category, mask_base64, now)
    )
    db.commit()

    return jsonify({
        "status": "ok",
        "path": mask_base64,      # 回傳 segmentation mask (base64)
        "category": category,
        "user_id": user_id
    })

@app.route('/wardrobe', methods=['GET'])
def wardrobe():
    user_id = request.args.get('user_id')
    category = request.args.get('category')
    if not user_id:
        return jsonify({"status": "error", "message": "缺少 user_id"}), 400

    db = get_db()
    query = "SELECT filename, category, mask_base64, created_at FROM wardrobe WHERE user_id = ?"
    params = [user_id]
    if category and category != "all":
        query += " AND category = ?"
        params.append(category)
    rows = db.execute(query, params).fetchall()

    images = []
    for row in rows:
        images.append({
            "path": row["mask_base64"],   # 前端會以 base64 顯示
            "category": row["category"],
            "filename": row["filename"],
            "created_at": row["created_at"]
        })

    return jsonify({"images": images})

@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    user_id = data.get('user_id')
    filenames = data.get('paths', [])
    if not user_id or not filenames:
        return jsonify({"status": "error", "message": "缺少 user_id 或 paths"}), 400

    db = get_db()
    deleted = 0
    for mask_base64 in filenames:
        db.execute(
            "DELETE FROM wardrobe WHERE user_id=? AND mask_base64=?",
            (user_id, mask_base64)
        )
        deleted += 1
    db.commit()
    return jsonify({"status": "ok", "deleted": deleted})

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Hugging Face Spaces Flask 運行中"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7860)
