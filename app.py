from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os, uuid, datetime
from werkzeug.utils import secure_filename
from google.cloud import storage, firestore
import json
from rembg import remove, new_session 
from io import BytesIO 

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app, supports_credentials=True)

DB_DIR = os.path.join("/tmp", "database") 
UPLOAD_FOLDER = os.path.join("/tmp", "uploads") 

os.makedirs(DB_DIR, exist_ok=True) 
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 

GCS_BUCKET = "cloths"  

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

_firestore_db_instance = None

def get_firestore_db():
    global _firestore_db_instance
    if _firestore_db_instance is None:
        _firestore_db_instance = firestore.Client()
        print("DEBUG: Firestore Client initialized.")
    return _firestore_db_instance

_rembg_session = None
def get_rembg_session():
    global _rembg_session
    if _rembg_session is None:
        os.environ['XDG_CACHE_HOME'] = '/tmp' 
        _rembg_session = new_session("u2net") 
        print("DEBUG: Rembg session initialized and model loaded.")
    return _rembg_session

def upload_image_to_gcs(local_path, bucket_name, data_bytes=None):
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    # 確保去背後的檔案是 PNG 格式，因為 rembg 輸出通常是 PNG
    # 這裡我們只使用 basename，不使用原始副檔名，直接指定為 .png
    blob_name = f"{uuid.uuid4().hex}_{os.path.splitext(os.path.basename(local_path))[0]}.png"
    blob = bucket.blob(blob_name)
    
    if data_bytes:
        blob.upload_from_string(data_bytes, content_type='image/png')
        print(f"DEBUG: Data bytes uploaded to GCS as {blob_name}.")
    else:
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

@app.route('/upload', methods=['POST'])
def upload():
    image = request.files.get('image')
    category = request.form.get('category')
    user_id = request.form.get('user_id')
    if not image or not category or not user_id:
        return jsonify({"status": "error", "message": "缺少必要參數"}), 400

    input_image_bytes = image.read()
    
    save_dir = os.path.join(UPLOAD_FOLDER, user_id, category)
    os.makedirs(save_dir, exist_ok=True)

    tags = ""
    temp_output_filepath = None 

    try:
        print("DEBUG: Starting background removal...")
        rembg_session = get_rembg_session()
        output_image_bytes = remove(input_image_bytes, session=rembg_session)
        print("DEBUG: Background removal completed.")

        # --- 新增: 檢查去背後圖片的位元組大小 ---
        print(f"DEBUG: Original image bytes size: {len(input_image_bytes)} bytes")
        print(f"DEBUG: Rembg output image bytes size: {len(output_image_bytes)} bytes")
        # --- 結束新增 ---

        # --- 新增: 臨時保存去背後的圖片，以便在日誌中確認 ---
        temp_output_filename = f"rembg_{uuid.uuid4().hex}.png"
        temp_output_filepath = os.path.join(save_dir, temp_output_filename)
        with open(temp_output_filepath, 'wb') as f:
            f.write(output_image_bytes)
        print(f"DEBUG: Rembg output temporarily saved to {temp_output_filepath}")
        # --- 結束新增 ---

        # 將去背後的圖片數據上傳到 GCS
        # 這裡我們只使用 temp_output_filepath 作為文件名參考，實際數據來自 output_image_bytes
        blob_name = upload_image_to_gcs(temp_output_filepath, GCS_BUCKET, data_bytes=output_image_bytes)

        db = get_firestore_db()
        doc_ref = db.collection('wardrobe').document(user_id).collection('items').document()
        doc_ref.set({
            'filename': blob_name,
            'category': category,
            'tags': tags,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        print(f"DEBUG: Image record saved to Firestore for user {user_id}: {blob_name}")

        signed_url = get_signed_url(GCS_BUCKET, blob_name)
        return jsonify({"status": "ok", "path": signed_url, "category": category, "tags": tags})
    except Exception as e:
        print(f"ERROR: Upload processing failed (including rembg): {e}")
        return jsonify({"status": "error", "message": f"上傳處理失敗: {e}"}), 500
    finally:
        if temp_output_filepath and os.path.exists(temp_output_filepath):
            os.remove(temp_output_filepath)
            print(f"DEBUG: Cleaned up temporary rembg output file: {temp_output_filepath}")
        pass 

@app.route('/wardrobe', methods=['GET'])
def wardrobe():
    user_id = request.args.get('user_id')
    category = request.args.get('category')
    if not user_id:
        return jsonify({"status": "error", "message": "缺少 user_id"}), 400

    images = []
    try:
        db = get_firestore_db()
        query = db.collection('wardrobe').document(user_id).collection('items')
        
        if category and category != "all":
            query = query.where('category', '==', category)
        
        query = query.order_by('timestamp', direction=firestore.Query.DESCENDING)
        
        docs = query.stream()
        
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
            query = db.collection('wardrobe').document(user_id).collection('items').where('filename', '==', filename)
            docs = query.stream()
            
            found_docs = 0
            for doc in docs:
                doc.reference.delete()
                print(f"DEBUG: Firestore document {doc.id} deleted for filename {filename}.")
                found_docs += 1
            
            if found_docs > 0:
                deleted_count += 1
            else:
                print(f"WARN: No Firestore document found for filename {filename} under user {user_id}.")

        except Exception as e:
            print(f"[WARN] 刪除失敗 (GCS 或 Firestore): {e}")

    return jsonify({"status": "ok", "deleted": deleted_count})

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Flask 伺服器運行中"})\

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
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
        
        try:
            get_rembg_session() 
            print("INFO: Rembg model pre-loaded on app startup.")
        except Exception as e:
            print(f"CRITICAL ERROR: Rembg model pre-load failed on app startup: {e}")

    app.run(host="0.0.0.0", port=port)
