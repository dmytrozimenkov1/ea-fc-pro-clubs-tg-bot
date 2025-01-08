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
    Calculates the relative time between now and the match time (short format).
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
                return f"{hours}h {minutes}m ago"
            else:
                return f"{hours}h ago"
        else:
            if minutes > 0:
                return f"{minutes}m ago"
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
    for club_id, club_data in match.clubs.items():
        try:
            goals_scored = int(club_data.goals)
        except ValueError:
            goals_scored = 0
        team_data = {
            'club_id': club_id,  # Add club_id here
            'team_name': club_data.details.name,
            'goals_scored': goals_scored
        }
        teams.append(team_data)
    match_info['teams'] = teams

    # Determine the Result for the Selected Club
    selected_club = next(
        (team for team in teams if team['club_id'] == selected_club_id), None
    )
    if not selected_club:
        match_info['result'] = 'unknown'
    else:
        selected_goals = selected_club['goals_scored']
        opponent = next(
            (team for team in teams if team['club_id'] != selected_club_id), None
        )
        opponent_goals = opponent['goals_scored'] if opponent else 0

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
    if selected_club_id in match.clubs:
        winner_by_dnf = match.clubs[selected_club_id].winnerByDnf
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

import prettytable as pt
from typing import List, Dict, Any, Optional
from fc_clubs_api.models import OverallStats
def format_matches(
        matches: List[Dict[str, Any]],
        club_name: str,
        overall_stats: Optional[OverallStats] = None,
        opposing_skill_ratings: Dict[str, Any] = {}
) -> str:
    """
    Formats the list of match dictionaries into a structured output with variable "sub-rows".
    """
    formatted_output = []

    if overall_stats:
        indicators = {
            'win': '🟩',
            'loss': '🟥',
            'draw': '⬜'
        }
        last_5_matches = matches[:5]
        last_5_results = [match['result'] for match in reversed(last_5_matches)]
        emojis = [indicators.get(result, '') for result in last_5_results]
        indicators_line = " ".join(emojis)

        overall_stats_line = f"{indicators_line}  Skill Rating: {overall_stats.skillRating}"
        wins_draws_losses = f"Wins/Draws/Losses: {overall_stats.wins}/{overall_stats.ties}/{overall_stats.losses}"
        formatted_output.append(overall_stats_line)
        formatted_output.append(wins_draws_losses)
        formatted_output.append("-" * 50)

    for match in matches:
        teams = match.get('teams', [])
        if len(teams) < 2:
            continue

        team1 = teams[0]
        team2 = teams[1]

        team1_name = team1['team_name']
        team2_name = team2['team_name']
        team1_goals = team1['goals_scored']
        team2_goals = team2['goals_scored']
        team1_id = team1['club_id']
        team2_id = team2['club_id']

        score = f"{team1_goals}:{team2_goals}"

        searched_team_name = ""
        opponent_team_name = ""
        searched_team_rating_value = None
        opponent_team_rating_value = None
        motm_name = None
        motm_rating = None
        opponent_motm_name = None
        opponent_motm_rating = None

        if team1_name.lower() == club_name.lower():
            searched_team_name = team1_name
            opponent_team_name = team2_name
            searched_team_rating_value = overall_stats.skillRating if overall_stats else None
            opponent_team_rating_value = opposing_skill_ratings.get(team2_id, None)
            for player in match.get('man_of_the_match', []):
                if player['team_name'].lower() == club_name.lower():
                    motm_name = player['player_name']
                    motm_rating = player['rating']
                elif player['team_name'].lower() == team2_name.lower():
                    opponent_motm_name = player['player_name']
                    opponent_motm_rating = player['rating']

        elif team2_name.lower() == club_name.lower():
            searched_team_name = team2_name
            opponent_team_name = team1_name
            searched_team_rating_value = overall_stats.skillRating if overall_stats else None
            opponent_team_rating_value = opposing_skill_ratings.get(team1_id, None)
            for player in match.get('man_of_the_match', []):
                if player['team_name'].lower() == club_name.lower():
                    motm_name = player['player_name']
                    motm_rating = player['rating']
                elif player['team_name'].lower() == team1_name.lower():
                    opponent_motm_name = player['player_name']
                    opponent_motm_rating = player['rating']
        else:
            searched_team_name = team1_name
            opponent_team_name = team2_name
            searched_team_rating_value = opposing_skill_ratings.get(team1_id, None)
            opponent_team_rating_value = opposing_skill_ratings.get(team2_id, None)

        # Добавляем перенос строки для длинных имен команд
        if len(searched_team_name) > 12:
            searched_team_name_lines = '\n'.join([searched_team_name[i:i+12] for i in range(0, len(searched_team_name), 12)])
        else:
            searched_team_name_lines = searched_team_name

        if len(opponent_team_name) > 12:
            opponent_team_name_lines = '\n'.join([opponent_team_name[i:i+12] for i in range(0, len(opponent_team_name), 12)])
        else:
            opponent_team_name_lines = opponent_team_name

        # Формируем строку MOTM с переносом, если необходимо
        motm_left_display = ""
        if motm_name is not None and motm_rating is not None:
            motm_combined = f"{motm_name} - {motm_rating}"
            if len(motm_combined) > 12:
                motm_left_display = '\n'.join(motm_combined[i:i + 12] for i in range(0, len(motm_combined), 12))
            else:
                motm_left_display = motm_combined

        motm_right_display = ""
        if opponent_motm_name is not None and opponent_motm_rating is not None:
            opponent_motm_combined = f"{opponent_motm_name} - {opponent_motm_rating}"
            if len(opponent_motm_combined) > 12:
                motm_right_display = '\n'.join(opponent_motm_combined[i:i + 12] for i in range(0, len(opponent_motm_combined), 12))
            else:
                motm_right_display = opponent_motm_combined

        relative_time = match.get('relative_time', 'N/A')

        table = pt.PrettyTable(header=False, padding_width=1)
        table.field_names = ["col1", "col2", "col3"]

        table.add_row([searched_team_name_lines, score, opponent_team_name_lines])

        # Добавляем рейтинги команд
        table.add_row([
            str(searched_team_rating_value) if searched_team_rating_value is not None else "",
            "",
            str(opponent_team_rating_value) if opponent_team_rating_value is not None else ""
        ])

        # Добавляем MOTM и рейтинг
        table.add_row([motm_left_display, "", motm_right_display])

        # table.add_row([relative_time, "", ""])
        table.add_row([relative_time, "", ""])

        formatted_output.append(table.get_string())

    return "\n".join(formatted_output)
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