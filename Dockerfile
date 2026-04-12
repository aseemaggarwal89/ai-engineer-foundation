FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app ./app

# Set working dir
WORKDIR /app

# ⭐ Debug-aware startup
CMD ["sh", "-c", "if [ \"$DEBUG\" = \"true\" ]; then \
  python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app.main:app --host 0.0.0.0 --port 8000; \
else \
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload; \
fi"]