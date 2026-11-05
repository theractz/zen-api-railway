# app.py
import os
import time
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# --- TAMBAHAN UNTUK CORS (IZIN BROWSER) ---
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    response = jsonify({"status": False, "error": str(e)})
    response.status_code = 500
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/ytplay', methods=['GET'])
def ytplay():
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"error": "Parameter 'v' wajib diisi"}), 400

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True, # Set False kalau mau lihat log lengkap
        'no_warnings': True,
        'noplaylist': True,
        # Konfigurasi PO Token Provider (Mengambil dari Environment Variable Railway)
        'extractor_args': {
            'youtubepot-bgutilhttp': {
                'base_url': os.environ.get('YOUTUBE_POT_PROVIDER_URL', 'http://127.0.0.1:4416')
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
