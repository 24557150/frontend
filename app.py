import os
import sqlite3
import tempfile
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.utils import secure_filename
from google.cloud import storage
import requests

app = Flask(__name__)
CORS(app)

# GCS 設定
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME") or "mwardrobe"
GCS_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
client = storage.Client.from_service_account_json(GCS_KEY_PATH)
bucket = client.bucket(GCS_BUCKET_NAME)

DATABASE = os.path.join(os.path.dirname(__file__), "database", "db.sqlite")
os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

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

def upload_to_gcs(local_path, destination_blob_name):
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_path)
    blob.make_public()
    return blob.public_url

def get_caption(local_path):
    # 請填寫你的 Hugging Face Space API URL
    BLIP_API_URL = "https://你的space名稱.hf.space/caption"
    try:
        with open(local_path, "rb") as f:
            files = {"image": f}
            response = requests.post(BLIP_API_URL, files=files, timeout=60)
        if response.status_code == 200:
            tags = response.json().get("caption", "(未取得描述)")
        else:
            tags = f"(描述失敗 {response.status_code})"
        return tags
    except Exception as e:
        print(f"[ERR] BLIP API 呼叫失敗: {e}")
        return "(描述錯誤)"

@app.route("/upload", methods=["POST"])
def upload():
    image = request.files.get("image")
    category = request.form.get("category")
    user_id = request.form.get("user_id")

    if not image or not category or not user_id:
        print("[ERR] 缺少必要參數")
        return jsonify({"status": "error", "message": "缺少必要參數"}), 400

    filename = secure_filename(image.filename)
    # 存成暫存檔
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        image.save(tmp.name)
        tmp_path = tmp.name
    print(f"[DEBUG] 暫存圖片路徑: {tmp_path}")

    # 取得描述
    tags = get_caption(tmp_path)
    print(f"[DEBUG] 取得形容詞描述: {tags}")

    # 上傳到 GCS
    gcs_path = f"{user_id}/{category}/{filename}"
    print(f"[DEBUG] 上傳 GCS 路徑: {gcs_path}")
    try:
        public_url = upload_to_gcs(tmp_path, gcs_path)
        print(f"[DEBUG] 上傳成功，public_url: {public_url}")
    except Exception as e:
        print(f"[ERR] GCS 上傳失敗: {e}")
        os.remove(tmp_path)
        return jsonify({"status": "error", "message": "GCS 上傳失敗"}), 500

    os.remove(tmp_path)

    # 寫入 SQLite
    db = get_db()
    db.execute(
        "INSERT INTO wardrobe (user_id, filename, category, tags) VALUES (?, ?, ?, ?)",
        (user_id, public_url, category, tags)
    )
    db.commit()

    return jsonify({
        "status": "ok",
        "path": public_url,
        "category": category,
        "tags": tags
    })

@app.route("/wardrobe", methods=["GET"])
def wardrobe():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"images": []})
    db = get_db()
    rows = db.execute(
        "SELECT id, filename, category, tags FROM wardrobe WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    images = [
        {
            "id": row["id"],
            "path": row["filename"],  # filename 其實就是 public_url
            "category": row["category"],
            "tags": row["tags"],
        }
        for row in rows
    ]
    return jsonify({"images": images})

@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_json()
    user_id = data.get("user_id")
    paths = data.get("urls", [])
    db = get_db()
    for path in paths:
        # 刪除 GCS 上的物件
        try:
            # 解析 GCS blob 路徑（從 public_url 取出 blob 名稱）
            idx = path.find(f"/{GCS_BUCKET_NAME}/")
            if idx != -1:
                blob_name = path[idx + len(GCS_BUCKET_NAME) + 2 :]
                blob = bucket.blob(blob_name)
                blob.delete()
                print(f"[DEBUG] 刪除 GCS: {blob_name}")
        except Exception as e:
            print(f"[ERR] 刪除 GCS 失敗: {e}")
        db.execute(
            "DELETE FROM wardrobe WHERE user_id = ? AND filename = ?",
            (user_id, path),
        )
    db.commit()
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
