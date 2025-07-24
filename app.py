from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os, uuid, datetime
from werkzeug.utils import secure_filename
from google.cloud import storage, firestore # 導入 firestore

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app, supports_credentials=True)

# Cloud Run 的 /tmp 目錄是唯一保證可寫入且適合臨時文件的位置。
UPLOAD_FOLDER = os.path.join("/tmp", "uploads") 

# 不需要 DATABASE 和 DB_DIR，因為我們將使用 Firestore
# DATABASE = os.path.join(DB_DIR, "db.sqlite")
# os.makedirs(DB_DIR, exist_ok=True) # 不再需要創建本地資料庫目錄

os.makedirs(UPLOAD_FOLDER, exist_ok=True) # 確保 /tmp/uploads 目錄存在

GCS_BUCKET = "cloths"  # 你的 bucket 名稱

# --- GCS Client 初始化邏輯 (保持不變) ---
_gcs_client_instance = None 

def get_gcs_client():
    global _gcs_client_instance
    if _gcs_client_instance is None:
        gcs_credentials_json = os.environ.get("GCP_SECRET_KEY")
        
        if gcs_credentials_json:
            try:
                credentials_info = json.loads(gcs_credentials_json)
                _gcs_client_instance = storage.Client.from_service_account_info(credentials_info)
                print("DEBUG: GCS Client initialized from GCP_SECRET_KEY (with private key).")
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse GCP_SECRET_KEY JSON: {e}")
                _gcs_client_instance = storage.Client()
                print("DEBUG: GCS Client initialized with default credentials due to JSON parse error.")
            except Exception as e:
                print(f"ERROR: Failed to initialize GCS Client from GCP_SECRET_KEY: {e}")
                _gcs_client_instance = storage.Client()
                print("DEBUG: GCS Client initialized with default credentials due to other initialization error.")
        else:
            _gcs_client_instance = storage.Client()
            print("DEBUG: GCS Client initialized with default credentials (no GCP_SECRET_KEY).")
    return _gcs_client_instance

# --- Firestore Client 初始化邏輯 ---
_firestore_db_instance = None

def get_firestore_db():
    global _firestore_db_instance
    if _firestore_db_instance is None:
        # Firestore Client 也會自動使用 GOOGLE_APPLICATION_CREDENTIALS
        # 或 Cloud Run 服務帳戶憑證。
        # 如果 GCP_SECRET_KEY 已設定，它將被用於 Firestore。
        _firestore_db_instance = firestore.Client()
        print("DEBUG: Firestore Client initialized.")
    return _firestore_db_instance

# @app.teardown_appcontext 不再需要關閉 SQLite 連接

# --- GCS 操作函式 (保持不變) ---
def upload_image_to_gcs(local_path, bucket_name):
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob_name = f"{uuid.uuid4().hex}_{os.path.basename(local_path)}"
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    print(f"DEBUG: File {local_path} uploaded to GCS as {blob_name}.")
    return blob_name

def get_signed_url(bucket_name, blob_name, expire_minutes=60):
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(
        version='v4',
        expiration=datetime.timedelta(minutes=expire_minutes),
        method='GET'
    )
    print(f"DEBUG: Generated signed URL for {blob_name}.")
    return url

# --- 路由部分 (修改為使用 Firestore) ---
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

    tags = ""

    try:
        blob_name = upload_image_to_gcs(filepath, GCS_BUCKET)

        # --- Firestore: 將圖片資訊儲存到 Firestore ---
        db = get_firestore_db()
        doc_ref = db.collection('wardrobe').document(user_id).collection('items').document()
        doc_ref.set({
            'filename': blob_name,
            'category': category,
            'tags': tags,
            'timestamp': firestore.SERVER_TIMESTAMP # 記錄上傳時間
        })
        print(f"DEBUG: Image record saved to Firestore for user {user_id}: {blob_name}")
        # --- 結束 Firestore 儲存 ---

        signed_url = get_signed_url(GCS_BUCKET, blob_name)
        return jsonify({"status": "ok", "path": signed_url, "category": category, "tags": tags})
    except Exception as e:
        print(f"ERROR: Upload processing failed: {e}")
        return jsonify({"status": "error", "message": f"上傳處理失敗: {e}"}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"DEBUG: Cleaned up local file: {filepath}")

@app.route('/wardrobe', methods=['GET'])
def wardrobe():
    user_id = request.args.get('user_id')
    category = request.args.get('category')
    if not user_id:
        return jsonify({"status": "error", "message": "缺少 user_id"}), 400

    images = []
    try:
        db = get_firestore_db()
        # --- Firestore: 從 Firestore 獲取圖片資訊 ---
        query = db.collection('wardrobe').document(user_id).collection('items')
        
        if category and category != "all":
            query = query.where('category', '==', category)
        
        # 可以選擇排序，例如按時間戳倒序
        query = query.order_by('timestamp', direction=firestore.Query.DESCENDING)
        
        docs = query.stream() # 獲取所有匹配的文件
        
        for doc in docs:
            item_data = doc.to_dict()
            blob_name = item_data.get('filename')
            if blob_name:
                signed_url = get_signed_url(GCS_BUCKET, blob_name)
                images.append({
                    "path": signed_url,
                    "category": item_data.get('category'),
                    "tags": item_data.get('tags') or ''
                })
        print(f"DEBUG: Retrieved {len(images)} images from Firestore for user {user_id}.")
        # --- 結束 Firestore 獲取 ---

    except Exception as e:
        print(f"ERROR: Failed to retrieve wardrobe from Firestore: {e}")
        return jsonify({"status": "error", "message": f"載入衣櫃失敗: {e}"}), 500

    return jsonify({"images": images})

@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    user_id = data.get('user_id')
    paths = data.get('paths', [])
    if not user_id or not paths:
        return jsonify({"status": "error", "message": "缺少 user_id 或 paths"}), 400

    deleted_count = 0
    db = get_firestore_db()
    
    for url in paths:
        if "storage.googleapis.com" in url:
            filename = url.split("/")[-1].split("?")[0]
        elif "X-Goog-Algorithm" in url:
            filename = url.split("/")[-1].split("?")[0]
        else:
            filename = url

        try:
            # --- GCS: 刪除實際的圖片檔案 ---
            client = get_gcs_client()
            bucket = client.bucket(GCS_BUCKET)
            blob = bucket.blob(filename)
            blob.delete()
            print(f"DEBUG: GCS blob {filename} deleted.")
            
            # --- Firestore: 找到並刪除 Firestore 中的記錄 ---
            # 由於 Firestore 沒有直接通過 filename 查詢並刪除的 API，
            # 我們需要先查詢，然後再刪除文件。
            # 這裡假設 filename (即 blob_name) 在 Firestore 記錄中是唯一的。
            query = db.collection('wardrobe').document(user_id).collection('items').where('filename', '==', filename)
            docs = query.stream()
            
            for doc in docs:
                doc.reference.delete()
                print(f"DEBUG: Firestore document {doc.id} deleted for filename {filename}.")
                deleted_count += 1
            
        except Exception as e:
            print(f"[WARN] 刪除失敗 (GCS 或 Firestore): {e}")

    return jsonify({"status": "ok", "deleted": deleted_count})

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Flask 伺服器運行中"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    # 在應用程式啟動時預先初始化 GCS 和 Firestore 客戶端
    with app.app_context():
        try:
            get_gcs_client()
            print("INFO: GCS Client successfully initialized on app startup.")
        except Exception as e:
            print(f"CRITICAL ERROR: GCS Client failed to initialize on app startup: {e}")
        
        try:
            get_firestore_db()
            print("INFO: Firestore Client successfully initialized on app startup.")
        except Exception as e:
            print(f"CRITICAL ERROR: Firestore Client failed to initialize on app startup: {e}")

    app.run(host="0.0.0.0", port=port)
