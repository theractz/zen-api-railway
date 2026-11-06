from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import traceback

app = Flask(__name__)
# Konfig CORS yang benar-benar menangani semua kasus
CORS(
    app,
    resources={r"/ytplay": {"origins": "*"}},
    methods=["GET"],
    allow_headers=["Content-Type"],
    supports_credentials=False
)

def get_youtube_cookies():
    """Ambil cookies dari env var"""
    cookies = os.getenv('YOUTUBE_COOKIES', '')
    cookie_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
    cookie_file.write(cookies.encode('utf-8'))
    cookie_file.close()
    return cookie_file.name

def cleanup_cookie_file(cookie_path):
    """Hapus file cookie sementara"""
    try:
        os.unlink(cookie_path)
    except:
        pass

@app.route('/ytplay', methods=['GET'])
def ytplay():
    video_id = request.args.get('v')
    if not video_id:
        response = jsonify({"status": False, "error": "Parameter 'v' (video ID) wajib diisi"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400

    cookie_path = get_youtube_cookies()

    # Konfigurasi yt-dlp yang sangat agresif
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/best',
        'cookiefile': cookie_path,

        # Client yang lebih stabil
        'player_client': ['android', 'mweb', 'embed'],

        # User-Agent untuk menghindari deteksi
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',

        # Header palsu
        'http_headers': {
            'Referer': 'https://www.youtube.com/',
            'Accept-Language': 'id-ID,en-US;q=0.9',
        },

        # Timeout dan retry
        'socket_timeout': 30,
        'retries': 3,
        'extract_flat': False,

        # Nonaktifkan logging yang bisa memicu deteksi
        'quiet': True,
        'no_warnings': True,

        # Konfigurasi POT Provider
        'extractor_args': {
            'youtube': {
                'po_token': os.getenv('YOUTUBE_POT_PROVIDER_URL', ''),
            }
        },

        # Nonaktifkan download, hanya ekstraksi URL
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f'https://www.youtube.com/watch?v={video_id}',
                download=False
            )

            cleanup_cookie_file(cookie_path)

            if 'url' not in info or not info['url']:
                response = jsonify({
                    "status": False,
                    "error": "Tidak dapat memperoleh URL audio",
                    "details": info
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 500

            response = jsonify({
                "status": True,
                "audio": info['url'],
                "title": info.get('title', ''),
                "duration": info.get('duration', 0),
                "format": info.get('ext', 'm4a')
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

    except Exception as e:
        cleanup_cookie_file(cookie_path)
        response = jsonify({
            "status": False,
            "error": f"Gagal memproses: {str(e)}",
            "traceback": traceback.format_exc()
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

if __name__ == '__main__':
    # Wajib membaca PORT dari Railway, jangan hardcode 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
