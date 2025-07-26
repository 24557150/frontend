FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pillow

COPY . .

RUN mkdir -p /tmp/outputs

ENV PORT=8080

CMD ["python", "RH05.py"]
