# Multi-stage build for Django with Tailwind CSS

# Stage 1: Build Tailwind CSS
FROM node:20-alpine AS tailwind-builder

WORKDIR /app

# Copy package files
COPY package.json ./
COPY package-lock.json* ./

# Install dependencies (use ci if package-lock exists, otherwise install)
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy static files needed for Tailwind
COPY static ./static
COPY templates ./templates
COPY tailwind.config.js ./

# Build Tailwind CSS
RUN npm run tw:build

# Stage 2: Python/Django application
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Copy compiled CSS from tailwind-builder stage
COPY --from=tailwind-builder /app/static/css/site.css ./static/css/site.css

# Create staticfiles directory
RUN mkdir -p staticfiles

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["gunicorn", "lyricslib.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
