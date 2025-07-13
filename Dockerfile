# Stage 1: Build Stage
FROM python:3.9-slim-buster as builder

WORKDIR /app

# Sistem bağımlılıklarını kur
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Poetry kur
RUN pip install poetry

# Sadece bağımlılık dosyalarını kopyala ve kur
# Bu, Docker katman önbelleklemesini (layer caching) optimize eder
COPY ../sentric-engine/pyproject.toml ./sentric-engine/
WORKDIR /app/sentric-engine
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-dev

# API bağımlılıklarını kur
WORKDIR /app
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---

# Stage 2: Production Stage
FROM python:3.9-slim-buster

# Sistem bağımlılıklarını kur (sadece runtime için gerekli olanlar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Builder aşamasından kurulan kütüphaneleri kopyala
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Uygulama kodunu kopyala
COPY ../sentric-engine/sentric_engine ./sentric_engine
COPY ./api ./api

# Model dosyalarını indir
RUN python -m sentric_engine.downloader

# Uygulamayı çalıştır
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]