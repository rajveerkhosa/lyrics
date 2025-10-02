# 1) Build static assets
FROM node:20-alpine AS assets
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 2) Python runtime
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# bring over built static assets
COPY --from=assets /app/static ./static
CMD bash -lc "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn lyricslib.wsgi:application --bind 0.0.0.0:$PORT"
