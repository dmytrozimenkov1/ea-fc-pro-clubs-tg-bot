# main.py

from fc_clubs_api.api import EAFCApiService
from fc_clubs_api.schemas import ClubSearchInput, Platform, MatchType, MatchesStatsInput, OverallStatsInput
from fc_clubs_api.models import Match, ClubInfo, MatchPlayersStats, OverallStats  # Updated import
from pydantic import ValidationError
from typing import List, Dict, Any, Optional
from datetime import datetime
from typing import Optional

def get_overall_stats(club_id: str, platform: Platform) -> Optional[OverallStats]:
    """
    Fetches the overall stats for a given club.

    Args:
        club_id (str): The ID of the club.
        platform (Platform): The platform enum value.

    Returns:
        Optional[OverallStats]: The overall stats of the club, or None if not found.
    """
    api_service = EAFCApiService()

    # Prepare input data for overall_stats API
    overall_stats_input = OverallStatsInput(
        clubIds=club_id,
        platform=platform
    )

    # Fetch overall stats
    overall_stats_response = api_service.overall_stats(overall_stats_input)

    if not overall_stats_response:
        return None

    # Assuming the API returns a list, return the first item
    return overall_stats_response[0]

def get_relative_time(match_datetime: datetime) -> str:
    """
    Calculates the relative time between now and the match time.

    Args:
        match_datetime (datetime): The datetime of the match.

    Returns:
        str: A string representing the relative time (e.g., "1 hour 15 mins ago").
    """
    now = datetime.now()
    difference = now - match_datetime

    if difference.days > 0:
        if difference.days == 1:
            return "1 day ago"
        else:
            return f"{difference.days} days ago"
    else:
        hours = difference.seconds // 3600
        minutes = (difference.seconds % 3600) // 60

        if hours > 0:
            if minutes > 0:
                return f"{hours} hours {minutes} mins ago"
            else:
                return f"{hours} hours ago"
        else:
            if minutes > 0:
                return f"{minutes} mins ago"
            else:
                return "just now"


def extract_match_info(match: Match, selected_club_id: str) -> Dict[str, Any]:
    """
    Extracts required information from a match.

    Args:
        match (Match): The match data.
        selected_club_id (str): The ID of the selected club.

    Returns:
        Dict[str, Any]: A dictionary containing extracted match information.
    """
    match_info = {}

    # Match ID
    match_info['match_id'] = match.matchId

    # Match Timestamp (converted to human-readable format)
    match_datetime = datetime.fromtimestamp(match.timestamp)
    match_info['match_timestamp'] = match_datetime.strftime('%Y-%m-%d %H:%M:%S')

    # Calculate Relative Time
    match_info['relative_time'] = get_relative_time(match_datetime)

    # Teams and Goals
    teams = []
    for club_id, club_info in match.clubs.items():
        try:
            goals_scored = int(club_info.goals)
        except ValueError:
            goals_scored = 0
        team_data = {
            'team_name': club_info.details.name,
            'goals_scored': goals_scored
        }
        teams.append(team_data)
    match_info['teams'] = teams

    # Determine the Result for the Selected Club
    selected_club_name = match.clubs[str(selected_club_id)].details.name  # Ensure club_id is string
    selected_goals = 0
    opponent_goals = 0

    for team in teams:
        if team['team_name'] == selected_club_name:
            selected_goals = team['goals_scored']
        else:
            opponent_goals = team['goals_scored']

    if selected_goals > opponent_goals:
        match_info['result'] = 'win'
    elif selected_goals < opponent_goals:
        match_info['result'] = 'loss'
    else:
        match_info['result'] = 'draw'

    # Man of the Match (MOTM) Details
    mom_players = []
    for club_id, players in match.players.items():
        for player_id, player_info in players.items():
            if player_info.mom == "1":
                try:
                    player_rating = float(player_info.rating)
                except ValueError:
                    player_rating = 0.0
                mom_players.append({
                    'player_name': player_info.playername,
                    'rating': player_rating,
                    'team_name': match.clubs[club_id].details.name
                })
    match_info['man_of_the_match'] = mom_players if mom_players else None

    # Winner by Disconnect for the Selected Club
    if str(selected_club_id) in match.clubs:
        winner_by_dnf = match.clubs[str(selected_club_id)].winnerByDnf
        match_info['winner_by_disconnect'] = True if winner_by_dnf == "1" else False
    else:
        match_info['winner_by_disconnect'] = None  # Club not part of this match

    return match_info


def get_matches_info(club_name: str, platform: Platform) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches and extracts match information for a given club.

    Args:
        club_name (str): The name of the club to search for.
        platform (Platform): The platform enum value.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of dictionaries containing match information,
                                        or None if no clubs/matches are found.
    """
    api_service = EAFCApiService()

    # Step 1: Search for the club
    input_data = ClubSearchInput(clubName=club_name, platform=platform)
    response = api_service.search_club(input_data)

    # Check if any clubs were found
    if not response:
        print("No clubs found matching the search criteria.")
        return None

    # Step 2: Select the first club from the search results
    selected_club = response[0]
    selected_club_id = selected_club.clubId

    # Step 3: Prepare input for fetching matches
    matches_input = MatchesStatsInput(
        clubIds=selected_club_id,
        platform=selected_club.platform,
        matchType=MatchType.LEAGUE_MATCH
    )

    # Step 4: Fetch league matches
    matches_response = api_service.matches_stats(matches_input)

    # Check if any matches were found
    if not matches_response:
        print("No league matches found for the selected club.")
        return None

    # Step 5: Parse and extract match information
    matches_info = []
    for match in matches_response:
        try:
            # Parse the match into the Match model
            parsed_match = Match.parse_obj(match)
        except ValidationError as e:
            print(f"Error parsing match data: {e}")
            continue  # Skip to the next match

        # Extract match information using the separate function
        match_info = extract_match_info(parsed_match, selected_club_id)
        matches_info.append(match_info)

    return matches_info

# main.py

def format_matches(matches: List[Dict[str, Any]], club_name: str, overall_stats: Optional[OverallStats] = None) -> str:
    """
    Formats the list of match dictionaries into a structured text with indicators and separators,
    including overall club stats if provided.

    Args:
        matches (List[Dict[str, Any]]): The list of match information dictionaries.
        club_name (str): The name of the selected club.
        overall_stats (Optional[OverallStats]): The overall statistics of the club.

    Returns:
        str: The formatted string containing overall stats and all matches with indicators and separators.
    """
    formatted_matches = []

    # Define the emoji indicators
    indicators = {
        'win': '🟩',
        'loss': '🟥',
        'draw': '⬜'
    }

    # Define fixed indentation for team names and score
    TEAM_INDENT = ""  # 4 spaces for indentation

    # If overall_stats is provided, format and add it
    if overall_stats:
        # Create the indicators line based on last 5 matches
        last_5_matches = matches[:5]
        last_5_results = [match['result'] for match in reversed(last_5_matches)]
        emojis = [indicators.get(result, '') for result in last_5_results]
        indicators_line = " ".join(emojis)

        # Format overall stats
        overall_stats_line = f"{indicators_line}  {overall_stats.skillRating}"
        wins_draws_losses = f"{overall_stats.wins}/{overall_stats.ties}/{overall_stats.losses}"

        # Append to formatted_matches
        formatted_matches.append(overall_stats_line)
        formatted_matches.append(wins_draws_losses)

    # Iterate through each match and format the information
    for match in matches:
        # Extract team information
        teams = match.get('teams', [])
        if len(teams) < 2:
            team_line = "Incomplete team information."
            motm_line = ""
            timestamp_line = f"{match.get('relative_time', '')}"
            formatted_matches.append(team_line)
            formatted_matches.append(timestamp_line)
            continue

        team1 = teams[0]['team_name']
        team2 = teams[1]['team_name']
        team1_goals = teams[0]['goals_scored']
        team2_goals = teams[1]['goals_scored']

        score = f"{team1_goals}:{team2_goals}"

        # Determine which team is the selected club
        if team1.lower() == club_name.lower():
            display_team1 = f"<b><u>{team1}</u></b>"
            display_team2 = team2
        elif team2.lower() == club_name.lower():
            display_team1 = team1
            display_team2 = f"<b><u>{team2}</u></b>"
        else:
            display_team1 = team1
            display_team2 = team2

        # Format the team line
        team_line = f"{TEAM_INDENT}{display_team1} {score} {display_team2}"

        # Extract Man of the Match (MOTM) information
        motm_list = match.get('man_of_the_match')
        motm_lines = []
        if motm_list:
            for mom in motm_list:
                mom_player = mom['player_name']
                mom_rating = mom['rating']
                mom_team_name = mom['team_name']

                if mom_team_name.lower() == team1.lower():
                    # Align MOTM under team1
                    motm_indent = " " * (len(TEAM_INDENT) + len(display_team1) + 1 + len(score) + 1)
                else:
                    # Align MOTM under team2
                    motm_indent = " " * (len(TEAM_INDENT) + len(display_team1) + 1 + len(score) + 1 + len(team2))

                motm_line = f"{motm_indent}{mom_player} - {mom_rating}"
                motm_lines.append(motm_line)
        else:
            # If no MOTM, display "MOTM: None"
            motm_lines.append(f"{TEAM_INDENT}MOTM: None")

        # Extract Winner by Disconnect information
        winner_by_disconnect = match.get('winner_by_disconnect')
        disconnect_line = "Disconnect" if winner_by_disconnect else ""

        # Extract Timestamp and Relative Time
        relative_time = match.get('relative_time', '')
        timestamp_line = f"{relative_time}"

        # Combine all parts
        parts = [team_line]
        parts.extend(motm_lines)
        parts.append(timestamp_line)
        if disconnect_line:
            parts.append(disconnect_line)

        # Join parts with newline
        formatted_match = "\n".join(parts)

        # Append to the list of formatted matches
        formatted_matches.append(formatted_match)

    # Skip the first separator
    return "\n_____________________\n".join(formatted_matches)

def main():
    """
    Main function to execute the script.
    """
    club_name = "Metallist"  # You can parameterize this as needed
    platform = Platform.COMMON_GEN5  # Adjust based on your platform enums

    # Create an instance of the API service
    api_service = EAFCApiService()

    # Step 1: Fetch match information
    matches_info = get_matches_info(club_name, platform)

    if matches_info is None:
        print("No matches to process.")
        return

    # Step 2: Format the matches with indicators and separators
    formatted_text = format_matches(matches_info, club_name)

    # Step 3: Save the formatted text to output.txt
    with open('output.txt', 'w', encoding='utf-8') as file:
        file.write(formatted_text)

    print("Match information has been saved to output.txt")

    # Step 4: Fetch and display overall stats of the club
    try:
        # Search for the club to get its ID
        input_data = ClubSearchInput(clubName=club_name, platform=platform)
        search_response = api_service.search_club(input_data)

        if not search_response:
            print("No clubs found matching the search criteria.")
            return

        selected_club = search_response[0]  # Select the first club
        selected_club_id = selected_club.clubId  # Get the club ID

        # Fetch overall stats using the club's ID
        overall_stats_input = MatchesStatsInput(
            clubIds=selected_club_id,
            platform=platform,
            matchType=MatchType.LEAGUE_MATCH  # Use a valid match type if necessary
        )
        overall_stats_response = api_service.overall_stats(overall_stats_input)

        print("\nOverall Club Stats:")
        for stat in overall_stats_response:
            print(f"Skill Rating: {stat.skillRating}")
            print(f"Wins: {stat.wins}")
            print(f"Draws (Ties): {stat.ties}")
            print(f"Losses: {stat.losses}")
            print("-" * 40)

    except Exception as e:
        print(f"An error occurred while fetching overall stats: {e}")


if __name__ == "__main__":
    main()
