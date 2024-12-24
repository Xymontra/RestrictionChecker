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

if __name__ == "__main__":
    app.run(debug=True)
