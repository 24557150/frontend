<<<<<<< HEAD
import os
import time
import requests
from urllib.parse import urljoin
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import nltk
from nltk import pos_tag, word_tokenize

# 初始化 NLTK
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# BLIP 模型
print("🔄 載入 BLIP 模型中...")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# 設定
BACKEND_URL = "https://liff-test-9xse.onrender.com"
USER_ID = "test_user"  # 可以改成你的 LINE user_id
CHECK_INTERVAL = 30  # 每 30 秒檢查一次
TEMP_FOLDER = "temp_images"
os.makedirs(TEMP_FOLDER, exist_ok=True)

def extract_adjectives(text):
    tokens = word_tokenize(text)
    tagged = pos_tag(tokens)
    return [word for word, pos in tagged if pos in ('JJ', 'JJR', 'JJS')]

def generate_tags(image_path):
    raw_image = Image.open(image_path).convert('RGB')
    inputs = processor(raw_image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    adjectives = extract_adjectives(caption)
    print(f"Caption: {caption}")
    return ",".join(adjectives)

def check_and_update_tags():
    print("🔍 檢查未標記的圖片...")
    res = requests.get(f"{BACKEND_URL}/wardrobe?user_id={USER_ID}")
    data = res.json()

    for img in data.get("images", []):
        if not img.get("tags"):  # tags 為空才處理
            img_url = urljoin(BACKEND_URL, img["path"])
            filename = os.path.basename(img["path"])
            category = img["category"]

            # 下載圖片
            img_path = os.path.join(TEMP_FOLDER, filename)
            with requests.get(img_url, stream=True) as r:
                with open(img_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)

            # 生成 tags
            tags = generate_tags(img_path)

            # 更新後端
            payload = {
                "user_id": USER_ID,
                "filename": filename,
                "category": category,
                "tags": tags
            }
            requests.post(f"{BACKEND_URL}/update_tags", json=payload)
            print(f"✅ 已補上 tags: {filename} -> {tags}")

            os.remove(img_path)  # 清除暫存檔

if __name__ == "__main__":
    while True:
        check_and_update_tags()
        time.sleep(CHECK_INTERVAL)
=======
import os
import time
import requests
from urllib.parse import urljoin
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import nltk
from nltk import pos_tag, word_tokenize

# 初始化 NLTK
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# BLIP 模型
print("🔄 載入 BLIP 模型中...")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# 設定
BACKEND_URL = "https://liff-test-9xse.onrender.com"
USER_ID = "test_user"  # 可以改成你的 LINE user_id
CHECK_INTERVAL = 30  # 每 30 秒檢查一次
TEMP_FOLDER = "temp_images"
os.makedirs(TEMP_FOLDER, exist_ok=True)

def extract_adjectives(text):
    tokens = word_tokenize(text)
    tagged = pos_tag(tokens)
    return [word for word, pos in tagged if pos in ('JJ', 'JJR', 'JJS')]

def generate_tags(image_path):
    raw_image = Image.open(image_path).convert('RGB')
    inputs = processor(raw_image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    adjectives = extract_adjectives(caption)
    print(f"Caption: {caption}")
    return ",".join(adjectives)

def check_and_update_tags():
    print("🔍 檢查未標記的圖片...")
    res = requests.get(f"{BACKEND_URL}/wardrobe?user_id={USER_ID}")
    data = res.json()

    for img in data.get("images", []):
        if not img.get("tags"):  # tags 為空才處理
            img_url = urljoin(BACKEND_URL, img["path"])
            filename = os.path.basename(img["path"])
            category = img["category"]

            # 下載圖片
            img_path = os.path.join(TEMP_FOLDER, filename)
            with requests.get(img_url, stream=True) as r:
                with open(img_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)

            # 生成 tags
            tags = generate_tags(img_path)

            # 更新後端
            payload = {
                "user_id": USER_ID,
                "filename": filename,
                "category": category,
                "tags": tags
            }
            requests.post(f"{BACKEND_URL}/update_tags", json=payload)
            print(f"✅ 已補上 tags: {filename} -> {tags}")

            os.remove(img_path)  # 清除暫存檔

if __name__ == "__main__":
    while True:
        check_and_update_tags()
        time.sleep(CHECK_INTERVAL)
>>>>>>> 2bbfa7a7c2328490db4598e217cfabed6bc0ed59
