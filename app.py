# app.py
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os, sqlite3, tempfile
from werkzeug.utils import secure_filename
from google.cloud import storage
from huggingface_hub import InferenceClient

app = Flask(__name__)
CORS(app, supports_credentials=True)

# === GCS 設定 ===
bucket_name = os.getenv("GCS_BUCKET_NAME")
gcp_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
client_gcs = storage.Client.from_service_account_json(gcp_credentials)
bucket = client_gcs.bucket(bucket_name)

# === Hugging Face BLIP 模型 ===
HF_TOKEN = os.environ.get("HF_TOKEN")
hf_client = InferenceClient(token=HF_TOKEN)

def upload_to_gcs(local_file, destination_path):
    blob = bucket.blob(destination_path)
    blob.upload_from_filename(local_file)
    blob.make_public()
    return blob.public_url

def get_caption(image_path):
    try:
        with open(image_path, "rb") as f:
            result = hf_client.image_to_text(
                model="Salesforce/blip-image-captioning-base",
                image=f
            )
            return result.get("generated_text", "")
    except Exception as e:
        print(f"BLIP API 調用錯誤: {e}")
        return ""

# === SQLite 設定 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DATABASE = os.path.join(DB_DIR, "db.sqlite")
os.makedirs(DB_DIR, exist_ok=True)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("""
        CREATE TABLE IF NOT EXISTS wardrobe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            gcs_url TEXT NOT NULL,
            category TEXT NOT NULL,
            tags TEXT
        )""")
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

    filename = secure_filename(image.filename)
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    image.save(tmp_path)

    tags = get_caption(tmp_path)

    gcs_path = f"{user_id}/{category}/{filename}"
    public_url = upload_to_gcs(tmp_path, gcs_path)

    db = get_db()
    db.execute(
        "INSERT INTO wardrobe (user_id, gcs_url, category, tags) VALUES (?, ?, ?, ?)",
        (user_id, public_url, category, tags)
    )
    db.commit()

    return jsonify({"status": "ok", "url": public_url, "category": category, "tags": tags})

@app.route('/wardrobe', methods=['GET'])
def wardrobe():
    user_id = request.args.get('user_id')
    category = request.args.get('category')
    if not user_id:
        return jsonify({"status": "error", "message": "缺少 user_id"}), 400

    db = get_db()
    query = "SELECT gcs_url, category, tags FROM wardrobe WHERE user_id = ?"
    params = [user_id]
    if category and category != "all":
        query += " AND category = ?"
        params.append(category)
    rows = db.execute(query, params).fetchall()

    return jsonify({"images": [
        {"url": row["gcs_url"], "category": row["category"], "tags": row["tags"] or ""}
        for row in rows
    ]})

@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    user_id = data.get('user_id')
    urls = data.get('urls', [])
    if not user_id or not urls:
        return jsonify({"status": "error", "message": "缺少 user_id 或 urls"}), 400

    db = get_db()
    deleted = 0
    for url in urls:
        if f"https://storage.googleapis.com/{bucket_name}/" in url:
            gcs_path = url.split(f"{bucket_name}/", 1)[-1]
            db.execute("DELETE FROM wardrobe WHERE user_id=? AND gcs_url=?", (user_id, url))
            blob = bucket.blob(gcs_path)
            blob.delete()
            deleted += 1
    db.commit()
    return jsonify({"status": "ok", "deleted": deleted})

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Flask with GCS storage & BLIP caption"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)