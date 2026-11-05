# app.py
import os
import traceback
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# --- 1. PERTAHANAN CORS (Wajib untuk Vercel) ---
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# --- 2. PERTAHANAN ERROR GLOBAL (Agar tidak crash & CORS hilang) ---
@app.errorhandler(Exception)
def handle_exception(e):
    # Cetak error asli ke log Railway
    print("=== SERVER ERROR ===")
    traceback.print_exc()
    
    # Kirim response JSON yang rapi, bukan halaman HTML error
    response = jsonify({
        "status": False, 
        "error": str(e),
        "message": "Terjadi kesalahan internal di server."
    })
    response.status_code = 500
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# --- 3. RUTE UTAMA ---
@app.route('/ytplay', methods=['GET'])
def ytplay():
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"status": False, "error": "Parameter 'v' (video ID) wajib diisi"}), 400

    # --- 4. STRATEGI BERLAPIS UNTUK YT-DLP ---
    # Kita coba beberapa konfigurasi jika yang pertama gagal
    strategies = [
        {
            # Strategi 1: Client Android VR (Paling jarang kena blokir)
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_vr', 'tv_embedded']
                }
            }
        },
        {
            # Strategi 2: Client Web dengan PO Token (Jika tersedia)
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['web']
                },
                'youtubepot-bgutilhttp': {
                    'base_url': os.environ.get('YOUTUBE_POT_PROVIDER_URL', 'http://127.0.0.1:4416')
                }
            }
        },
        {
            # Strategi 3: Format 'best' (Cadangan terakhir, ambil video+audio)
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_vr', 'tv_embedded', 'web']
                }
            }
        }
    ]

    # Tambahkan cookies ke semua strategi jika ada
    cookie_path = '/app/cookies.txt'
    if os.path.exists(cookie_path):
        for strat in strategies:
            strat['cookiefile'] = cookie_path

    last_error = "Tidak ada strategi yang berhasil."

    for i, ydl_opts in enumerate(strategies):
        try:
            print(f"[STRATEGI {i+1}] Mencoba client: {ydl_opts.get('extractor_args', {}).get('youtube', {}).get('player_client', ['default'])}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
                
                # Ambil URL audio
                audio_url = None
                if 'url' in info:
                    audio_url = info['url']
                elif 'formats' in info:
                    # Kalau info utama tidak punya URL, cari di daftar formats
                    for f in info['formats']:
                        if f.get('acodec') != 'none':
                            audio_url = f.get('url')
                            break
                
                if audio_url:
                    print(f"[STRATEGI {i+1}] ✅ Berhasil!")
                    return jsonify({
                        "status": True,
                        "result": {
                            "title": info.get('title', ''),
                            "duration": info.get('duration', 0),
                            "audio": audio_url,
                            "source": f"railway-strategy-{i+1}"
                        }
                    })
                else:
                    last_error = "Format audio tidak ditemukan di info."
                    print(f"[STRATEGI {i+1}] ❌ Gagal: {last_error}")

        except Exception as e:
            last_error = str(e)
            print(f"[STRATEGI {i+1}] ❌ Error: {last_error}")
            # Lanjut ke strategi berikutnya
            continue

    # Jika semua strategi gagal
    return jsonify({
        "status": False, 
        "error": f"Semua strategi gagal. Error terakhir: {last_error}"
    }), 500

if __name__ == '__main__':
    # Jalankan server Flask
    app.run(host='0.0.0.0', port=5000)