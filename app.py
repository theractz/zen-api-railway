import os
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)

# 1. IZIN CORS PALING AMAN
CORS(app, resources={r"/*": {"origins": "*"}})

# 2. FUNGSI EKSTRAKSI DENGAN PENYAMARAN (SPOOFING)
def get_audio_url(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Kita paksa pakai client TV dan Web Embedded (sering lolos dari blokir bot)
    clients = ["tv_embedded", "web_embedded", "mweb"]
    
    base_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "geo_bypass": True,
        
        # --- TRIK PENYAMARAN USER-AGENT ---
        # Pura-pura jadi browser Chrome asli
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-us,en;q=0.5",
            "Sec-Fetch-Mode": "navigate"
        },
        
        # Pastikan path cookies benar
        "cookiefile": "/app/cookies.txt" if os.path.exists("/app/cookies.txt") else None
    }

    last_error = None

    for client in clients:
        opts = base_opts.copy()
        opts["extractor_args"] = {
            "youtube": {
                "player_client": [client]
            }
        }

        try:
            print(f"[YT-DLP] Mencoba client: {client}...")
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Ambil URL audio
                if "url" in info:
                    print(f"[YT-DLP] ✅ Berhasil dengan client: {client}")
                    return {
                        "status": True,
                        "audio": info["url"],
                        "title": info.get("title"),
                        "duration": info.get("duration"),
                        "client": client
                    }
                
                formats = info.get("formats", [])
                audio_formats = [f for f in formats if f.get("acodec") != "none"]
                if audio_formats:
                    best = max(audio_formats, key=lambda x: x.get("abr") or 0)
                    print(f"[YT-DLP] ✅ Berhasil (fallback) dengan client: {client}")
                    return {
                        "status": True,
                        "audio": best["url"],
                        "title": info.get("title"),
                        "duration": info.get("duration"),
                        "client": client
                    }
                
                print(f"[YT-DLP] ❌ Client {client} tidak menemukan format audio.")

        except Exception as e:
            last_error = str(e)
            print(f"[YT-DLP] ❌ Client {client} gagal: {last_error}")
            continue

    raise Exception(f"Semua client gagal. Error terakhir: {last_error}")

# 3. RUTE UTAMA
@app.route('/ytplay', methods=['GET'])
def ytplay():
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"status": False, "error": "Parameter 'v' wajib diisi"}), 400

    try:
        result = get_audio_url(video_id)
        return jsonify({"status": True, "result": result})
    except Exception as e:
        print("=== ERROR TERJADI ===")
        traceback.print_exc()
        return jsonify({"status": False, "error": str(e)}), 500

# 4. ERROR HANDLER GLOBAL
@app.errorhandler(Exception)
def handle_exception(e):
    print("=== GLOBAL ERROR ===")
    traceback.print_exc()
    response = jsonify({"status": False, "error": str(e)})
    response.status_code = 500
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)