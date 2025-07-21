說明
🔹 frontend/
index.html：使用者上傳衣服，選擇分類（上衣、褲子等）

detect.html：上傳全身照 → 分割 → 推薦相似衣服

history.html：顯示查詢歷史（查詢時間、輸入圖片、推薦結果）

🔹 backend/
Flask API：

/upload：接收上傳衣服

/detect：接收穿搭照 → 分割 → 找出相似衣服

/history：儲存查詢與讀取查詢紀錄

model/：可放衣物比對邏輯，例如顏色特徵、embedding

utils/：

    分割模型（如 rembg）

    處理圖片儲存、分類查詢


pip install -r requirements.venv.txt

安裝
pip install transformers torch torchvision pillow nltk
