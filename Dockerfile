# 1. 選用官方 python image
FROM python:3.10-slim

# 2. 設定時區/locale
ENV TZ=Asia/Taipei

# 3. 安裝 pip 更新與系統依賴 (包含 onnxruntime 和 rembg 所需的庫)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libopenblas-dev \
    liblapack-dev \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. 複製程式碼與 requirements.txt
WORKDIR /app
COPY . /app

# 5. 安裝 Python 套件
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 6. 設定 Cloud Run 監聽 port
ENV PORT 8080

# 7. 執行 Gunicorn 作為啟動指令 (調整 worker 和 threads 以優化圖像處理性能)
# workers 1, threads 4 允許一個 worker 進程處理多個請求，適合 I/O 密集型或 CPU 密集型但有等待的任務
# timeout 600 秒 (10 分鐘) 允許模型有足夠時間處理較大的圖片
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 600 app:app

