# 1. 選用官方 python image
FROM python:3.10-slim

# 2. 設定時區/locale（亞洲用戶可加這行，可選）
ENV TZ=Asia/Taipei

# 3. 安裝 pip 更新與系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. 複製程式碼與 requirements.txt
WORKDIR /app
COPY . /app

# 5. 安裝 Python 套件
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# 6. 設定 Cloud Run 監聽 port
ENV PORT 8080

# 7. 執行 Gunicorn 作為啟動指令
CMD exec gunicorn --bind :$PORT --workers 2 --timeout 600 app:app

