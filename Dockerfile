FROM python:3.11-slim

# Install FFmpeg dan dependensi Node.js (dibutuhkan PO Token Provider)
RUN apt-get update && apt-get install -y ffmpeg curl nodejs npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install --upgrade yt-dlp

# Copy sisa file (termasuk app.py dan cookies.txt)
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]