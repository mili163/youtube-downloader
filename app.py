from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid
import threading
import time
from datetime import datetime

app = Flask(__name__)

# תיקיית הורדות זמניות
DOWNLOAD_DIR = '/tmp/youtube_downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# מילון לניהול הורדות פעילות
active_downloads = {}

def cleanup_old_files():
    """מחיקת קבצים ישנים מדי דקה"""
    while True:
        try:
            for filename in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(filepath):
                    # מחיקת קבצים שישנים מ-10 דקות
                    if time.time() - os.path.getmtime(filepath) > 600:
                        os.remove(filepath)
        except Exception as e:
            print(f"Error in cleanup: {e}")
        time.sleep(60)

# הפעלת ניקוי קבצים ברקע
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/api/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get('url')
        quality = data.get('quality', 'best')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # יצירת מזהה ייחודי להורדה
        download_id = str(uuid.uuid4())
        
        # הגדרות yt-dlp
        output_template = os.path.join(DOWNLOAD_DIR, f'{download_id}.%(ext)s')
        
        ydl_opts = {
            'format': quality,
            'outtmpl': output_template,
            'extractaudio': False,
        }
        
        # אם מבקשים אודיו בלבד
        if data.get('audio_only'):
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
        
        # הורדת הסרטון
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            # ביצוע ההורדה
            ydl.download([url])
        
        # מציאת הקובץ שהורד
        downloaded_file = None
        for file in os.listdir(DOWNLOAD_DIR):
            if file.startswith(download_id):
                downloaded_file = file
                break
        
        if not downloaded_file:
            return jsonify({'error': 'Download failed'}), 500
        
        return jsonify({
            'success': True,
            'download_id': download_id,
            'filename': downloaded_file,
            'title': title,
            'duration': duration
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<download_id>')
def get_file(download_id):
    try:
        # מציאת הקובץ
        for filename in os.listdir(DOWNLOAD_DIR):
            if filename.startswith(download_id):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                # שליחת הקובץ עם מחיקה אוטומטית אחרי השליחה
                return send_file(filepath, as_attachment=True, 
                               download_name=filename)
        
        return jsonify({'error': 'File not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/info', methods=['POST'])
def get_video_info():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
        return jsonify({
            'title': info.get('title'),
            'duration': info.get('duration'),
            'uploader': info.get('uploader'),
            'view_count': info.get('view_count'),
            'formats': [
                {
                    'quality': f.get('height', 'audio'),
                    'ext': f.get('ext'),
                    'filesize': f.get('filesize')
                }
                for f in info.get('formats', [])[:10]  # מגביל ל-10 פורמטים
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
3.2 הפעלת השרת
bash# הפעלה רגילה לבדיקה
python3 app.py

# הפעלה עם Gunicorn לייצור
gunicorn -w 2 -b 0.0.0.0:5000 app:app
