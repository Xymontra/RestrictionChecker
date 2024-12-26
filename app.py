import os
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from flask_cors import CORS

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
        
# Firebase 
firebase_config = os.getenv("FIREBASE_CONFIG")
if not firebase_config:
    raise ValueError("Firebase yapılandırması bulunamadı. Lütfen 'FIREBASE_CONFIG' ortam değişkenini ayarlayın.")

# JSON string
firebase_cred = json.loads(firebase_config)

# Firebase Admin
cred = credentials.Certificate(firebase_cred)
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://restrictioncheckerdb-default-rtdb.europe-west1.firebasedatabase.app"
})

@app.route("/log_usage", methods=["POST"])
def log_usage():
    try:
        ref = db.reference("usage_logs")
        ref.push({"timestamp": datetime.now().isoformat()})
        return jsonify({"status": "success", "message": "Usage logged"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/get_usage", methods=["GET"])
def get_usage():
    try:
        ref = db.reference("usage_logs")
        data = ref.get()
        if data:
            usage_data = [{"timestamp": value["timestamp"]} for key, value in data.items()]
            return jsonify(usage_data)
        else:
            return jsonify([])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
