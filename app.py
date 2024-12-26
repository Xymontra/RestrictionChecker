import json
from datetime import datetime
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, origins=["https://restrictionchecker.onrender.com", "https://restrictionviewer.netlify.app"])

# API Key'i alın
API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("YouTube API Key bulunamadı. Lütfen YOUTUBE_API_KEY çevre değişkenini ayarlayın.")

youtube = build('youtube', 'v3', developerKey=API_KEY)

@app.route("/")
def home():
    return "YouTube Restriction Checker API is running!"

@app.route("/check_video", methods=["POST"])
def check_video():
    try:
        data = request.get_json()
        video_url = data.get("video_url")
        if not video_url:
            return jsonify({"error": "Video URL is required"}), 400

        if "v=" in video_url:
            video_id = video_url.split("v=")[-1].split("&")[0]
        else:
            return jsonify({"error": "Invalid YouTube URL"}), 400

        request_data = youtube.videos().list(
            part="contentDetails,status",
            id=video_id
        )
        response = request_data.execute()

        if not response.get("items"):
            return jsonify({"error": "Video not found"}), 404

        video_info = response["items"][0]
        restrictions = video_info.get("contentDetails", {}).get("regionRestriction", {})
        embeddable = video_info.get("status", {}).get("embeddable", True)

        return jsonify({
            "status": "success",
            "restrictions": restrictions,
            "embeddable": embeddable
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/healthz", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Backend is running"})

@app.route("/check_youtube", methods=["GET"])
def check_youtube():
    try:
        # Test amaçlı bir video ID'si kullanıyoruz
        test_video_id = "lZ9hUrTrgTc"  # Örnek bir video ID
        request_data = youtube.videos().list(
            part="id",
            id=test_video_id
        )
        response = request_data.execute()

        # Eğer bir sonuç dönerse API çalışıyor demektir
        if "items" in response and len(response["items"]) > 0:
            return jsonify({"status": "Operational"}), 200
        else:
            return jsonify({"status": "Error"}), 500
    except Exception as e:
        # Hata durumunda detaylı bilgi döner
        return jsonify({"status": "Error", "message": str(e)}), 
        
# Kullanım verilerini tutmak için bir JSON dosyası
USAGE_LOG_FILE = "usage_log.json"

# Kullanım verilerini yükle
def load_usage_data():
    try:
        with open(USAGE_LOG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Kullanım verilerini kaydet
def save_usage_data(data):
    with open(USAGE_LOG_FILE, "w") as f:
        json.dump(data, f)

@app.route("/log_usage", methods=["POST"])
def log_usage():
    usage_data = load_usage_data()
    usage_data.append({"timestamp": datetime.now().isoformat()})
    save_usage_data(usage_data)
    return jsonify({"status": "success", "message": "Usage logged"})

@app.route("/get_usage", methods=["GET"])
def get_usage():
    usage_data = load_usage_data()
    return jsonify(usage_data)

if __name__ == "__main__":
    app.run(debug=True)
