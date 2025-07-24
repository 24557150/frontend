from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os, sqlite3, uuid, datetime
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

GCS_BUCKET = "cloths"  # 你的 bucket 名稱

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
    return blob_name

def get_signed_url(bucket_name, blob_name, expire_minutes=60):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(
        version='v4',
        expiration=datetime.timedelta(minutes=expire_minutes),
        method='GET'
    )
    return url

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

    tags = ""  # caption/tags 先不使用

    # 上傳到 Cloud Storage
    blob_name = upload_image_to_gcs(filepath, GCS_BUCKET)

    db = get_db()
    db.execute(
        "INSERT INTO wardrobe (user_id, filename, category, tags) VALUES (?, ?, ?, ?)",
        (user_id, blob_name, category, tags)
    )
    db.commit()

    signed_url = get_signed_url(GCS_BUCKET, blob_name)
    return jsonify({"status": "ok", "path": signed_url, "category": category, "tags": tags})

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

    images = []
    for row in rows:
        signed_url = get_signed_url(GCS_BUCKET, row['filename'])
        images.append({
            "path": signed_url,
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
        if "storage.googleapis.com" in url:
            filename = url.split("/")[-1].split("?")[0]
        elif "X-Goog-Algorithm" in url:
            filename = url.split("/")[-1].split("?")[0]
        else:
            filename = url

        try:
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET)
            blob = bucket.blob(filename)
            blob.delete()
        except Exception as e:
            print(f"[WARN] GCS 刪除失敗: {e}")

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
