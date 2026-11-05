# app.py
import os
import subprocess
import time
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# Jalankan PO Token Provider di background saat server start
print("Menjalankan PO Token Provider...")
# Tunggu sebentar agar provider siap
time.sleep(3)

@app.route('/ytplay', methods=['GET'])
def ytplay():
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"error": "Parameter 'v' wajib diisi"}), 400

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': False, # Set True kalau sudah stabil
        'no_warnings': True,
        'noplaylist': True,
        # Konfigurasi PO Token Provider
        'extractor_args': {
            'youtubepot-bgutilhttp': {
                'base_url': 'http://127.0.0.1:4416'
            }
        },
        # Pakai cookies kalau ada
        'cookiefile': '/app/cookies.txt' if os.path.exists('/app/cookies.txt') else None
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            
            # Ambil URL audio
            audio_url = info.get('url')
            if not audio_url:
                raise Exception("Format audio tidak ditemukan")

            return jsonify({
                "status": True,
                "result": {
                    "title": info.get('title', ''),
                    "duration": info.get('duration', 0),
                    "audio": audio_url,
                    "source": "railway-ytdlp"
                }
            })
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)