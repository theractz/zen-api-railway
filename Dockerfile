# Dockerfile Baru untuk Railway
FROM python:3.11-slim

# Install dependensi sistem
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ffmpeg \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install flask flask-cors yt-dlp \
    && pip install bgutil-ytdlp-pot-provider

# Verifikasi ffmpeg
RUN ffmpeg -version

# Copy file project
COPY . /app
WORKDIR /app

# Environment variables (di set di Railway)
# YOUTUBE_COOKIES
# YOUTUBE_POT_PROVIDER_URL

# Jalankan server
CMD ["python", "app.py"]
