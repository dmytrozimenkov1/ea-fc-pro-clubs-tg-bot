import os
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from database import get_all_users
from main import get_matches_info, get_overall_stats, format_matches
from fc_clubs_api.schemas import Platform, ClubSearchInput
from fc_clubs_api.api import EAFCApiService
from telegram.error import TelegramError

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
        # Fetch match information
        matches_info = get_matches_info(team_name, platform)

        if not matches_info:
            message = f"⚠️ No matches found for the club <b>{team_name}</b>."
        else:
            # Initialize API service
            api_service = EAFCApiService()

            # Search for the club to get its ID
            input_data = ClubSearchInput(clubName=team_name, platform=platform)
            search_response = api_service.search_club(input_data)

            if not search_response:
                message = f"⚠️ No clubs found matching the name <b>{team_name}</b>."
            else:
                selected_club = search_response[0]
                selected_club_id = selected_club.clubId

                # Fetch overall stats using the club's ID
                overall_stats = get_overall_stats(selected_club_id, platform)

                if not overall_stats:
                    overall_stats_message = "⚠️ No overall stats found for the specified club."
                    logger.warning(overall_stats_message)
                    # Proceed without overall_stats
                    overall_stats = None

                # **New Steps to Include Opposing Teams' Skill Ratings**

                # 1. Collect all unique opposing club IDs
                opposing_club_ids = set()
                for match in matches_info:
                    for team in match['teams']:
                        if team['club_id'] != selected_club_id:
                            opposing_club_ids.add(team['club_id'])

                # 2. Fetch skill ratings for opposing clubs
                opposing_skill_ratings = {}
                for club_id in opposing_club_ids:
                    club_stats = get_overall_stats(club_id, platform)
                    if club_stats:
                        try:
                            skill_rating = int(club_stats.skillRating)
                        except ValueError:
                            skill_rating = "N/A"
                        opposing_skill_ratings[club_id] = skill_rating
                    else:
                        opposing_skill_ratings[club_id] = "N/A"

                # 3. Format the matches with indicators and separators, including overall stats and opposing skill ratings
                message = format_matches(
                    matches_info,
                    team_name,
                    overall_stats,
                    opposing_skill_ratings  # Pass the skill ratings mapping
                )

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
