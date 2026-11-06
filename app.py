from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import traceback

app = Flask(__name__)
# Izinkan Vercel (atau web lain) buat nembak API ini
CORS(app, resources={r"/*": {"origins": "*"}})

def get_youtube_cookies():
    cookies = os.getenv('YOUTUBE_COOKIES', '').strip()
    if not cookies:
        return None
    if not cookies.startswith('# Netscape'):
        cookies = '# Netscape HTTP Cookie File\n' + cookies
    cookie_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8')
    cookie_file.write(cookies)
    cookie_file.close()
    return cookie_file.name

def cleanup_cookie_file(cookie_path):
    if cookie_path:
        try:
            os.unlink(cookie_path)
        except:
            pass

@app.route('/ytplay', methods=['GET'])
def ytplay():
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"status": False, "error": "Parameter 'v' wajib diisi"}), 400

    cookie_path = get_youtube_cookies()
    pot_url = os.getenv('YOUTUBE_POT_PROVIDER_URL', '').strip()

    print(f"\n[INFO] Memproses Video ID: {video_id}")
    print(f"[INFO] PO Token URL: {pot_url}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'cookiefile': cookie_path,
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
        'socket_timeout': 30,
        'retries': 5,                # Coba 5x kalau koneksi putus
        'extractor_retries': 5,      # Coba 5x kalau YouTube minta reload (error tadi)
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                # tv dan mweb biasanya paling stabil kalau pakai PO Token
                'player_client': ['tv', 'mweb', 'web_safari']
            },
            'youtubepot-bgutilhttp': {
                'base_url': [pot_url]
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[INFO] Mencoba mengekstrak audio...")
            info = ydl.extract_info(
                f'https://www.youtube.com/watch?v={video_id}',
                download=False
            )
            cleanup_cookie_file(cookie_path)

            if 'url' not in info or not info['url']:
                print("[ERROR] URL audio tidak ditemukan di response.")
                return jsonify({"status": False, "error": "Tidak dapat memperoleh URL audio"}), 500

            print(f"[SUKSES] Dapet URL audio untuk: {info.get('title', '')}")
            return jsonify({
                "status": True,
                "audio": info['url'],
                "title": info.get('title', ''),
                "duration": info.get('duration', 0),
                "format": info.get('ext', 'm4a')
            })

    except Exception as e:
        cleanup_cookie_file(cookie_path)
        print(f"[ERROR] Gagal: {str(e)}")
        return jsonify({
            "status": False,
            "error": f"Gagal memproses: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080)) # Railway default port
    app.run(host='0.0.0.0', port=port)
