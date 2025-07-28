from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os, uuid, datetime, sys
from werkzeug.utils import secure_filename
from google.cloud import storage, firestore
import json
from rembg import remove, new_session
from io import BytesIO
import traceback # 導入 traceback 模組
import shutil # 導入 shutil 用於刪除目錄

# 導入 RunningHubImageProcessor (現在從新的檔案名稱 runninghub_processor.py 導入)
try:
    from runninghub_processor import RunningHubImageProcessor # <--- 這裡已修改
    print("INFO: Successfully imported RunningHubImageProcessor from runninghub_processor.py.")
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import RunningHubImageProcessor. Make sure runninghub_processor.py is in your project and accessible: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    RunningHubImageProcessor = None

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app, supports_credentials=True)

UPLOAD_FOLDER = os.path.join("/tmp", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GCS_BUCKET = "cloths"

# 從環境變數獲取 RunningHub API Key，避免寫死在程式碼中
# 注意：如果 runninghub_processor.py 內部也硬編碼了 Key，則以 runninghub_processor.py 內部為準
POSE_API_KEY = os.environ.get("POSE_API_KEY", "dcbfc7a79ccb45b89cea62cdba512755")
if POSE_API_KEY == "dcbfc7a79ccb45b89cea62cdba512755":
    print("WARN: POSE_API_KEY is not set in environment variables or using default placeholder. Pose correction may fail.", file=sys.stderr)

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
                print(f"ERROR: Failed to parse GCP_SECRET_KEY JSON: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                _gcs_client_instance = storage.Client()
                print("DEBUG: GCS Client initialized with default credentials due to JSON parse error.")
            except Exception as e:
                print(f"ERROR: Failed to initialize GCS Client from GCP_SECRET_KEY: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
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
        try:
            print("DEBUG: Setting XDG_CACHE_HOME to /tmp for rembg model cache.")
            os.environ['XDG_CACHE_HOME'] = '/tmp'
            print("DEBUG: Attempting to initialize rembg session with 'u2net' model...")
            _rembg_session = new_session("u2net")
            print("DEBUG: Rembg session initialized and model loaded successfully.")
        except Exception as e:
            print(f"CRITICAL ERROR: Rembg model initialization failed: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            raise
    return _rembg_session

def upload_image_to_gcs(local_path, bucket_name, data_bytes=None):
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
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

        print(f"DEBUG: Original image bytes size: {len(input_image_bytes)} bytes")
        print(f"DEBUG: Rembg output image bytes size: {len(output_image_bytes)} bytes")

        temp_output_filename = f"rembg_{uuid.uuid4().hex}.png"
        temp_output_filepath = os.path.join(save_dir, temp_output_filename)
        with open(temp_output_filepath, 'wb') as f:
            f.write(output_image_bytes)
        print(f"DEBUG: Rembg output temporarily saved to {temp_output_filepath}")

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
        print(f"ERROR: Upload processing failed (including rembg): {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
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
        print(f"ERROR: Failed to retrieve wardrobe from Firestore: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
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
            client = get_gcs_client()
            bucket = client.bucket(GCS_BUCKET)
            blob = bucket.blob(filename)
            blob.delete()
            print(f"DEBUG: GCS blob {filename} deleted.")

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
            print(f"[WARN] 刪除失敗 (GCS 或 Firestore): {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

    return jsonify({"status": "ok", "deleted": deleted_count})

@app.route('/upload_wannabe', methods=['POST'])
def upload_wannabe():
    image = request.files.get('image')
    user_id = request.form.get('user_id')
    if not image or not user_id:
        return jsonify({"status": "error", "message": "缺少必要參數 (image 或 user_id)"}), 400

    input_image_bytes = image.read()

    save_dir = os.path.join(UPLOAD_FOLDER, user_id, "wannabe")
    os.makedirs(save_dir, exist_ok=True)

    temp_output_filepath = None

    try:
        print("DEBUG: Starting background removal for wannabe image...")
        rembg_session = get_rembg_session()
        output_image_bytes = remove(input_image_bytes, session=rembg_session)
        print("DEBUG: Background removal completed for wannabe image.")

        temp_output_filename = f"rembg_wannabe_{uuid.uuid4().hex}.png"
        temp_output_filepath = os.path.join(save_dir, temp_output_filename)
        with open(temp_output_filepath, 'wb') as f:
            f.write(output_image_bytes)
        print(f"DEBUG: Rembg output temporarily saved to {temp_output_filepath}")

        blob_name = upload_image_to_gcs(temp_output_filepath, GCS_BUCKET, data_bytes=output_image_bytes)

        db = get_firestore_db()
        doc_ref = db.collection('wannabe_wardrobe').document(user_id).collection('items').document()
        doc_ref.set({
            'filename': blob_name,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        print(f"DEBUG: Wannabe image record saved to Firestore for user {user_id}: {blob_name}")

        signed_url = get_signed_url(GCS_BUCKET, blob_name)
        return jsonify({"status": "ok", "path": signed_url})
    except Exception as e:
        print(f"ERROR: Wannabe image upload processing failed (including rembg): {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return jsonify({"status": "error", "message": f"上傳「我想成為」圖片失敗: {e}"}), 500
    finally:
        if temp_output_filepath and os.path.exists(temp_output_filepath):
            os.remove(temp_output_filepath)
            print(f"DEBUG: Cleaned up temporary rembg wannabe output file: {temp_output_filepath}")


@app.route('/wannabe_wardrobe', methods=['GET'])
def wannabe_wardrobe():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "缺少 user_id"}), 400

    images = []
    try:
        db = get_firestore_db()
        query = db.collection('wannabe_wardrobe').document(user_id).collection('items')
        query = query.order_by('timestamp', direction=firestore.Query.DESCENDING)

        docs = query.stream()

        for doc in docs:
            item_data = doc.to_dict()
            blob_name = item_data.get('filename')
            if blob_name:
                signed_url = get_signed_url(GCS_BUCKET, blob_name)
                images.append({
                    "path": signed_url,
                    "tags": item_data.get('tags', '')
                })
        print(f"DEBUG: Retrieved {len(images)} wannabe images from Firestore for user {user_id}.")

    except Exception as e:
        print(f"ERROR: Failed to retrieve wannabe wardrobe from Firestore: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return jsonify({"status": "error", "message": f"載入「我想成為」圖片失敗: {e}"}), 500

    return jsonify({"images": images})

@app.route('/delete_wannabe', methods=['POST'])
def delete_wannabe():
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
            client = get_gcs_client()
            bucket = client.bucket(GCS_BUCKET)
            blob = bucket.blob(filename)
            blob.delete()
            print(f"DEBUG: GCS blob {filename} deleted for wannabe.")

            query = db.collection('wannabe_wardrobe').document(user_id).collection('items').where('filename', '==', filename)
            docs = query.stream()

            found_docs = 0
            for doc in docs:
                doc.reference.delete()
                print(f"DEBUG: Firestore document {doc.id} deleted for wannabe filename {filename}.")
                found_docs += 1

            if found_docs > 0:
                deleted_count += 1
            else:
                print(f"WARN: No Firestore document found for wannabe filename {filename} under user {user_id}.")

        except Exception as e:
            print(f"[WARN] Failed to delete wannabe image (GCS or Firestore): {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

    return jsonify({"status": "ok", "deleted": deleted_count})

@app.route('/pose_correction', methods=['POST'])
def pose_correction():
    if RunningHubImageProcessor is None:
        print("ERROR: RunningHubImageProcessor is not available. Pose correction aborted.", file=sys.stderr)
        return jsonify({"status": "error", "message": "姿勢矯正模型未載入或導入失敗"}), 500

    image = request.files.get('image')
    if not image:
        return jsonify({"status": "error", "message": "缺少圖片"}), 400

    save_path = f"/tmp/{uuid.uuid4().hex}_{secure_filename(image.filename)}"
    image_bytes = image.read()
    with open(save_path, 'wb') as f:
        f.write(image_bytes)
    print(f"DEBUG: Original image saved to {save_path} for pose correction.")

    output_dir = "/tmp/pose_results_rh"
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 使用 POSE_API_KEY 環境變數，並設定 base_url 為 https://www.runninghub.cn
        processor = RunningHubImageProcessor(api_key=POSE_API_KEY, base_url="https://www.runninghub.cn")
        print(f"DEBUG: Initialized RunningHubImageProcessor with base_url: {processor.base_url}")

        # --- 多步驟調用 RunningHub API ---
        # 1. 上傳圖片
        uploaded_filename = processor.upload_image(save_path)
        if not uploaded_filename:
            print("ERROR: RunningHub image upload failed.", file=sys.stderr)
            return jsonify({"status": "error", "message": "姿勢矯正失敗：圖片上傳到 RunningHub 失敗"}), 500

        # 2. 創建任務
        task_id = processor.create_task(uploaded_filename, prompt_text="姿勢矯正")
        if not task_id:
            print("ERROR: RunningHub task creation failed.", file=sys.stderr)
            return jsonify({"status": "error", "message": "姿勢矯正失敗：創建 RunningHub 任務失敗"}), 500

        # 3. 等待任務完成
        if not processor.wait_for_completion(task_id, max_wait_time=300):
            print("ERROR: RunningHub task did not complete successfully or timed out.", file=sys.stderr)
            return jsonify({"status": "error", "message": "姿勢矯正失敗：RunningHub 任務超時或未成功完成"}), 500

        # 4. 獲取結果
        results = processor.get_task_results(task_id)
        if not results:
            print("ERROR: RunningHub failed to get task results.", file=sys.stderr)
            return jsonify({"status": "error", "message": "姿勢矯正失敗：獲取 RunningHub 結果失敗"}), 500

        # 5. 保存結果 (下載到本地)
        saved_local_paths = processor.save_results(results, output_dir=output_dir)

        if saved_local_paths:
            result_path = saved_local_paths[0]
            print(f"DEBUG: Pose correction result generated locally at {result_path}")

            blob_name = upload_image_to_gcs(result_path, GCS_BUCKET)
            signed_url = get_signed_url(GCS_BUCKET, blob_name)
            print(f"INFO: Pose correction successful. Result URL: {signed_url}")
            return jsonify({"status": "ok", "result": signed_url})
        else:
            print("WARN: Pose correction succeeded but no output image found locally.", file=sys.stderr)
            return jsonify({"status": "error", "message": "姿勢矯正失敗：未生成圖片"}), 500
    except Exception as e:
        print(f"ERROR: Pose correction failed: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return jsonify({"status": "error", "message": f"姿勢矯正過程中發生錯誤: {e}"}), 500
    finally:
        if os.path.exists(save_path):
            os.remove(save_path)
            print(f"DEBUG: Cleaned up temporary input file: {save_path}")
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            print(f"DEBUG: Cleaned up temporary pose results directory: {output_dir}")


@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Flask 伺服器運行中"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    try:
        with app.app_context():
            try:
                get_gcs_client()
                print("INFO: GCS Client successfully initialized on app startup.")
            except Exception as e:
                print(f"CRITICAL ERROR: GCS Client failed to initialize on app startup: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

            try:
                get_firestore_db()
                print("INFO: Firestore Client successfully initialized on app startup.")
            except Exception as e:
                print(f"CRITICAL ERROR: Firestore Client failed to initialize on app startup: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

            try:
                get_rembg_session()
                print("INFO: Rembg model pre-loaded on app startup.")
            except Exception as e:
                print(f"CRITICAL ERROR: Rembg model pre-load failed on app startup: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        print(f"CRITICAL ERROR: Application failed to start: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
