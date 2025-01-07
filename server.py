import os
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from database import get_all_users
from main import get_matches_info, format_matches
from fc_clubs_api.schemas import Platform

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN is not set in environment variables.")
    exit(1)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


@app.route('/notify', methods=['POST'])
def notify():
    """
    Endpoint to notify all users about a team's latest matches.
    Expects a JSON payload with the 'team_name' field.
    """
    data = request.get_json()
    if not data or 'team_name' not in data:
        return jsonify({"error": "Missing 'team_name' in request payload."}), 400

    team_name = data['team_name'].strip()
    if not team_name:
        return jsonify({"error": "'team_name' cannot be empty."}), 400

    platform = Platform.COMMON_GEN5  # Adjust as needed or make it dynamic

    try:
        matches_info = get_matches_info(team_name, platform)
        if not matches_info:
            message = f"⚠️ No matches found for the club <b>{team_name}</b>."
        else:
            message = format_matches(matches_info, team_name)
    except Exception as e:
        logger.error(f"Error fetching match information: {e}")
        return jsonify({"error": "Failed to fetch match information."}), 500

    users = get_all_users()
    if not users:
        return jsonify({"message": "No subscribed users to notify."}), 200

    def send_message(user_id, text):
        payload = {
            "chat_id": user_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            response = requests.post(TELEGRAM_API_URL, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Notification sent to {user_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send notification to {user_id}: {e}")
            return False

    sent_count = 0
    failed_count = 0
    for user_id in users:
        if send_message(user_id, message):
            sent_count += 1
        else:
            failed_count += 1

    return jsonify({
        "message": f"Notifications sent to {sent_count} users. {failed_count} failed.",
        "total_users": len(users),
        "sent": sent_count,
        "failed": failed_count
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
