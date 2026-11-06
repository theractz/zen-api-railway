from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import traceback

app = Flask(__name__)

# Konfigurasi CORS paling aman
CORS(app, resources={r"/*": {"origins": "*"}})

def get_youtube_cookies():
    """Ambil cookies dari env var dan simpan ke file temporary"""
    cookies = os.getenv('YOUTUBE_COOKIES', '').strip()
    if not cookies:
        return None
    
    # Pastikan format Netscape valid
    if not cookies.startswith('# Netscape'):
        cookies = '# Netscape HTTP Cookie File\n' + cookies
        
    cookie_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8')
    cookie_file.write(cookies)
    cookie_file.close()
    return cookie_file.name

def cleanup_cookie_file(cookie_path):
    """Hapus file cookie sementara"""
    if cookie_path:
        try:
            os.unlink(cookie_path)
        except:
            pass

@app.route('/ytplay', methods=['GET'])
def ytplay():
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"status": False, "error": "Parameter 'v' (video ID) wajib diisi"}), 400

    cookie_path = get_youtube_cookies()
    
    # Ambil URL PO Token dari Environment Variable Railway
    pot_url = os.getenv('YOUTUBE_POT_PROVIDER_URL', '')

    # Konfigurasi yt-dlp dengan PO Token Provider
    ydl_opts = {
        'format': 'bestaudio/best',
        'cookiefile': cookie_path,
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
        'socket_timeout': 30,
        'retries': 3,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['tv_embedded', 'web_embedded'], # Client yang lebih longgar
                'po_token': 'bgutil:http' # Memberitahu yt-dlp untuk pakai PO Token
            },
            'youtubepot-bgutilhttp': {
                'base_url': pot_url # URL server PO Token dari Railway
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f'https://www.youtube.com/watch?v={video_id}',
                download=False
            )

            cleanup_cookie_file(cookie_path)

            if 'url' not in info or not info['url']:
                return jsonify({
                    "status": False,
                    "error": "Tidak dapat memperoleh URL audio"
                }), 500

            return jsonify({
                "status": True,
                "audio": info['url'],
                "title": info.get('title', ''),
                "duration": info.get('duration', 0),
                "format": info.get('ext', 'm4a')
            })

    except Exception as e:
        cleanup_cookie_file(cookie_path)
        return jsonify({
            "status": False,
            "error": f"Gagal memproses: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    # Wajib membaca PORT dari Railway
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
