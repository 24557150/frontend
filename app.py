from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os, sqlite3, base64, requests, uuid
from werkzeug.utils import secure_filename
from google.cloud import storage

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app, supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
DATABASE = os.path.join(DB_DIR, "db.sqlite")
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GCS_BUCKET = "mwardrobe"  # 你的 bucket 名稱

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
        print(f"[DEBUG] Caption result: {caption}")
        return caption
    except Exception as e:
        print(f"[ERROR] BLIP API 調用錯誤: {e}")
        return ""

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

def upload_image_to_gcs(local_path, bucket_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob_name = f"{uuid.uuid4().hex}_{os.path.basename(local_path)}"
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    blob.make_public()
    return blob.public_url

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

    # 調用 BLIP 模型生成 caption
    tags = get_caption(filepath)

    # 上傳到 Cloud Storage
    gcs_url = upload_image_to_gcs(filepath, GCS_BUCKET)

    db = get_db()
    db.execute(
        "INSERT INTO wardrobe (user_id, filename, category, tags) VALUES (?, ?, ?, ?)",
        (user_id, filename, category, tags)
    )
    db.commit()

    # 回傳 GCS 圖片網址
    return jsonify({"status": "ok", "path": gcs_url, "category": category, "tags": tags})

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

    # 注意：這裡用 GCS 圖片網址（你也可存在 DB，但這版用規則拼出，或用前端吃 /upload 回傳的 path）
    images = []
    for row in rows:
        # 這邊其實建議存下 gcs_url 到 db，這樣刪除時才能對應，不然只能用 filename 硬拼
        images.append({
            # "path": f"/static/uploads/{user_id}/{row['category']}/{row['filename']}", # 原本本地路徑
            "path": f"https://storage.googleapis.com/{GCS_BUCKET}/{row['filename']}",   # GCS 網址
            "category": row['category'],
            "tags": row['tags'] or ''
        })

    return jsonify({"images": images})

@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    user_id = data.get('user_id')
    paths = data.get('paths', [])
    if not user_id or not paths:
        return jsonify({"status": "error", "message": "缺少 user_id 或 paths"}), 400

    db = get_db()
    deleted = 0
    for url in paths:
        # GCS 圖片網址格式 https://storage.googleapis.com/mwardrobe/xxx.png
        if url.startswith(f"https://storage.googleapis.com/{GCS_BUCKET}/"):
            filename = url.split(f"/{GCS_BUCKET}/")[-1]
            try:
                client = storage.Client()
                bucket = client.bucket(GCS_BUCKET)
                blob = bucket.blob(filename)
                blob.delete()
            except Exception as e:
                print(f"[WARN] GCS 刪除失敗: {e}")
            # 刪 DB（假設 DB 仍以 filename 當 key）
            db.execute(
                "DELETE FROM wardrobe WHERE user_id=? AND filename=?",
                (user_id, filename)
            )
            deleted += 1
    db.commit()
    return jsonify({"status": "ok", "deleted": deleted})

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Flask 伺服器運行中"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

