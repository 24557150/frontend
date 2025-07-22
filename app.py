import os, sqlite3, base64, requests, tempfile
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.utils import secure_filename
from google.cloud import storage

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app, supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DATABASE = os.path.join(DB_DIR, "db.sqlite")
os.makedirs(DB_DIR, exist_ok=True)

# Google Cloud Storage
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
client = storage.Client.from_service_account_json(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
bucket = client.bucket(BUCKET_NAME)

# Hugging Face Space API
BLIP_API_URL = "https://yushon-blip-caption-service.hf.space/run/predict"

def get_caption(image_path):
    try:
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        response = requests.post(BLIP_API_URL, json={
            "data": [f"data:image/png;base64,{img_b64}"]
        }, timeout=60)
        result = response.json()
        caption = ""
        if isinstance(result, dict) and "data" in result and isinstance(result["data"], list):
            caption = result["data"][0]
        return caption
    except Exception as e:
        print(f"[ERROR] BLIP API 調用錯誤: {e}")
        return ""

def upload_to_gcs(local_path, dest_blob_name):
    blob = bucket.blob(dest_blob_name)
    blob.upload_from_filename(local_path)
    blob.make_public()
    return f"https://storage.googleapis.com/{BUCKET_NAME}/{dest_blob_name}"

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("""
        CREATE TABLE IF NOT EXISTS wardrobe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            category TEXT NOT NULL,
            tags TEXT
        )""")
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

@app.route('/upload', methods=['POST'])
def upload():
    image = request.files.get('image')
    category = request.form.get('category')
    user_id = request.form.get('user_id')
    if not image or not category or not user_id:
        return jsonify({"status": "error", "message": "缺少必要參數"}), 400

    # 存到暫存檔
    filename = secure_filename(image.filename)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        image.save(tmp.name)
        tmp_path = tmp.name

    # 跑 BLIP 模型
    tags = get_caption(tmp_path)

    # 上傳 GCS (user_id/category/filename)
    gcs_path = f"{user_id}/{category}/{filename}"
    public_url = upload_to_gcs(tmp_path, gcs_path)
    os.remove(tmp_path)

    db = get_db()
    db.execute(
        "INSERT INTO wardrobe (user_id, filename, category, tags) VALUES (?, ?, ?, ?)",
        (user_id, public_url, category, tags)
    )
    db.commit()

    return jsonify({"status": "ok", "path": public_url, "category": category, "tags": tags})

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

    return jsonify({
        "images": [
            {
                "path": row['filename'],  # 這裡直接存GCS URL
                "category": row['category'],
                "tags": row['tags'] or ''
            } for row in rows
        ]
    })

@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    user_id = data.get('user_id')
    paths = data.get('paths', [])
    if not user_id or not paths:
        return jsonify({"status": "error", "message": "缺少 user_id 或 paths"}), 400

    db = get_db()
    deleted = 0
    for gcs_url in paths:
        # gcs_url 格式 https://storage.googleapis.com/BUCKET_NAME/user_id/category/filename
        try:
            # 刪 GCS
            rel_path = gcs_url.split(f"https://storage.googleapis.com/{BUCKET_NAME}/")[-1]
            blob = bucket.blob(rel_path)
            blob.delete()
        except Exception as e:
            print("[WARN] 刪除GCS失敗", e)
        db.execute("DELETE FROM wardrobe WHERE user_id=? AND filename=?", (user_id, gcs_url))
        deleted += 1
    db.commit()
    return jsonify({"status": "ok", "deleted": deleted})

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Flask 伺服器運行中（GCS儲存）"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
