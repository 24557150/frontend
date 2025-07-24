from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os, sqlite3, uuid, datetime
from werkzeug.utils import secure_filename
from google.cloud import storage
import json # 確保有導入 json 模組

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app, supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")

# --- 關鍵修改 1: 將 UPLOAD_FOLDER 指向 /tmp/uploads，這是 Cloud Run 推薦的臨時路徑 ---
UPLOAD_FOLDER = os.path.join("/tmp", "uploads") 

DATABASE = os.path.join(DB_DIR, "db.sqlite")

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # 確保 /tmp/uploads 目錄存在

GCS_BUCKET = "cloths"  # 你的 bucket 名稱

# --- 關鍵修改 2: GCS Client 初始化邏輯 ---
# 這裡我們將創建一個全域的 GCS Client 實例，確保它使用正確的憑證
_gcs_client_instance = None 

def get_gcs_client():
    global _gcs_client_instance
    if _gcs_client_instance is None:
        # 嘗試從環境變數 GCP_SECRET_KEY 獲取 JSON 憑證字符串
        gcs_credentials_json = os.environ.get("GCP_SECRET_KEY")
        
        if gcs_credentials_json:
            try:
                # 直接解析 JSON 字符串
                credentials_info = json.loads(gcs_credentials_json)
                # 使用解析後的憑證資訊來初始化 Client
                _gcs_client_instance = storage.Client.from_service_account_info(credentials_info)
                print("DEBUG: GCS Client initialized from GCP_SECRET_KEY.")
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse GCP_SECRET_KEY JSON: {e}")
                # 如果解析失敗，則回退到預設憑證（這會導致簽名失敗，但至少應用程式不會崩潰）
                _gcs_client_instance = storage.Client()
                print("DEBUG: GCS Client initialized with default credentials due to JSON parse error.")
            except Exception as e:
                print(f"ERROR: Failed to initialize GCS Client from GCP_SECRET_KEY: {e}")
                _gcs_client_instance = storage.Client()
                print("DEBUG: GCS Client initialized with default credentials due to other initialization error.")
        else:
            # 如果沒有 GCP_SECRET_KEY 環境變數，則使用預設的應用程式預設憑證 (ADC)
            # 在 Cloud Run 上，這通常是 Compute Engine 服務帳戶，但不能用於簽名
            _gcs_client_instance = storage.Client()
            print("DEBUG: GCS Client initialized with default credentials (no GCP_SECRET_KEY).")
    return _gcs_client_instance

# ... (get_db 和 close_db 函式不變)

def upload_image_to_gcs(local_path, bucket_name):
    client = get_gcs_client() # 使用我們上面定義的獲取客戶端函式
    bucket = client.bucket(bucket_name)
    blob_name = f"{uuid.uuid4().hex}_{os.path.basename(local_path)}"
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    print(f"DEBUG: File {local_path} uploaded to GCS as {blob_name}.")
    return blob_name

def get_signed_url(bucket_name, blob_name, expire_minutes=60):
    client = get_gcs_client() # 使用我們上面定義的獲取客戶端函式
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(
        version='v4',
        expiration=datetime.timedelta(minutes=expire_minutes),
        method='GET'
    )
    print(f"DEBUG: Generated signed URL for {blob_name}.")
    return url

@app.route('/upload', methods=['POST'])
def upload():
    image = request.files.get('image')
    category = request.form.get('category')
    user_id = request.form.get('user_id')
    if not image or not category or not user_id:
        return jsonify({"status": "error", "message": "缺少必要參數"}), 400

    # `save_dir` 現在會位於 /tmp 下
    save_dir = os.path.join(UPLOAD_FOLDER, user_id, category)
    os.makedirs(save_dir, exist_ok=True)

    filename = secure_filename(image.filename)
    filepath = os.path.join(save_dir, filename)
    image.save(filepath)

    tags = "" # 保持為空

    try:
        # 上傳到 Cloud Storage，取得 blob 名稱
        blob_name = upload_image_to_gcs(filepath, GCS_BUCKET)

        db = get_db()
        db.execute(
            "INSERT INTO wardrobe (user_id, filename, category, tags) VALUES (?, ?, ?, ?)",
            (user_id, blob_name, category, tags)
        )
        db.commit()

        # 回傳 GCS 簽名網址
        signed_url = get_signed_url(GCS_BUCKET, blob_name)
        return jsonify({"status": "ok", "path": signed_url, "category": category, "tags": tags})
    except Exception as e:
        # 捕捉 GCS 相關的錯誤，並返回 JSON 格式的錯誤訊息
        print(f"ERROR: Upload processing failed: {e}")
        return jsonify({"status": "error", "message": f"上傳處理失敗: {e}"}), 500
    finally:
        # 清理臨時文件：上傳到 GCS 後刪除本地文件
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"DEBUG: Cleaned up local file: {filepath}")

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
        # 這裡也可能需要簽名 URL，所以確保 get_signed_url 使用正確的 Client
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
            client = get_gcs_client() # 使用我們上面定義的獲取客戶端函式
            bucket = client.bucket(GCS_BUCKET)
            blob = bucket.blob(filename)
            blob.delete()
            print(f"DEBUG: GCS blob {filename} deleted.")
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
    # Cloud Run 預設將 PORT 設定為 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)