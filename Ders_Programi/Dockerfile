FROM python:3.9-slim

WORKDIR /app

# Gerekli paketleri yükle
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Gereksinimleri kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Migrations klasörü oluştur
RUN mkdir -p migrations

# Uygulama çalıştırma komutu
ENV FLASK_APP=app.py
ENV PYTHONPATH=/app

EXPOSE 5000

# Uygulama çalıştırma komutu
CMD ["flask", "run", "--host=0.0.0.0"] 