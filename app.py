from flask import Flask, request, jsonify
from googleapiclient.discovery import build
import os

app = Flask(__name__)

# YouTube API Key
API_KEY = os.getenv("YOUTUBE_API_KEY")

# Hata: API Key yoksa uygulamayı başlatma
if not API_KEY:
    raise ValueError("YouTube API Key bulunamadı. Lütfen YOUTUBE_API_KEY değişkenini ayarlayın.")

# YouTube API servisini başlat
youtube = build('youtube', 'v3', developerKey=API_KEY)

@app.route("/")
def home():
    return "YouTube Restriction Checker API is running!"

@app.route("/check_video", methods=["POST"])
def check_video():
    try:
        # Kullanıcıdan video URL'sini al
        data = request.get_json()
        video_url = data.get("video_url")
        
        if not video_url:
            return jsonify({"error": "Video URL is required"}), 400
        
        # Video ID'yi URL'den ayıkla
        if "v=" in video_url:
            video_id = video_url.split("v=")[-1].split("&")[0]
        else:
            return jsonify({"error": "Invalid YouTube URL"}), 400

        # YouTube API'den video bilgilerini al
        request_data = youtube.videos().list(
            part="contentDetails,status",
            id=video_id
        )
        response = request_data.execute()

        if not response.get("items"):
            return jsonify({"error": "Video not found"}), 404

        video_info = response["items"][0]
        restrictions = video_info.get("contentDetails", {}).get("regionRestriction", {})

        return jsonify({
            "status": "success",
            "restrictions": restrictions
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
