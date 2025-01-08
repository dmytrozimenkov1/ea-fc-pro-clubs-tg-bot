# fc_clubs_api/models.py

from pydantic import BaseModel
from typing import Dict, List,Optional

# --- Custom Models ---

class CustomKit(BaseModel):
    stadName: str
    kitId: str
    seasonalTeamId: str
    seasonalKitId: str
    selectedKitType: str
    customKitId: str
    customAwayKitId: str
    customThirdKitId: str
    customKeeperKitId: str
    kitColor1: str
    kitColor2: str
    kitColor3: str
    kitColor4: str
    kitAColor1: str
    kitAColor2: str
    kitAColor3: str
    kitAColor4: str
    kitThrdColor1: str
    kitThrdColor2: str
    kitThrdColor3: str
    kitThrdColor4: str
    dCustomKit: str
    crestColor: str
    crestAssetId: str

class SingleClubInfo(BaseModel):
    name: str
    clubId: int
    regionId: int
    teamId: int
    customKit: CustomKit

# --- Updated ClubInfo as a Standard BaseModel ---

class ClubInfo(BaseModel):
    name: str
    clubId: int
    regionId: int
    teamId: int
    customKit: CustomKit

# --- Other Models ---

class Club(BaseModel):
    clubId: str
    wins: str
    losses: str
    ties: str
    gamesPlayed: str
    gamesPlayedPlayoff: str
    goals: str
    goalsAgainst: str
    cleanSheets: str
    points: str
    reputationtier: str
    clubInfo: ClubInfo
    platform: str
    clubName: str
    currentDivision: str

class OverallStats(BaseModel):
    clubId: str
    bestDivision: Optional[str] = None
    bestFinishGroup: Optional[str] = None
    finishesInDivision1Group1: str
    finishesInDivision2Group1: str
    finishesInDivision3Group1: str
    finishesInDivision4Group1: str
    finishesInDivision5Group1: str
    finishesInDivision6Group1: str
    gamesPlayed: str
    gamesPlayedPlayoff: str
    goals: str
    goalsAgainst: str
    promotions: str
    relegations: str
    losses: str
    ties: str
    wins: str
    lastMatch0: str
    lastMatch1: str
    lastMatch2: str
    lastMatch3: str
    lastMatch4: str
    lastMatch5: str
    lastMatch6: str
    lastMatch7: str
    lastMatch8: str
    lastMatch9: str
    lastOpponent0: str
    lastOpponent1: str
    lastOpponent2: str
    lastOpponent3: str
    lastOpponent4: str
    lastOpponent5: str
    lastOpponent6: str
    lastOpponent7: str
    lastOpponent8: str
    lastOpponent9: str
    wstreak: str
    unbeatenstreak: str
    skillRating: str
    reputationtier: str
    leagueAppearances: str
class MemberCareerStatsMember(BaseModel):
    name: str
    proPos: str
    gamesPlayed: str
    goals: str
    assists: str
    manOfTheMatch: str
    ratingAve: str
    prevGoals: str
    favoritePosition: str

class MemberCareerStatsPositionCount(BaseModel):
    midfielder: int
    goalkeeper: int
    forward: int
    defender: int

class MemberCareerStats(BaseModel):
    members: List[MemberCareerStatsMember]
    positionCount: MemberCareerStatsPositionCount

class MemberStatsMember(BaseModel):
    name: str
    gamesPlayed: str
    winRate: str
    goals: str
    assists: str
    cleanSheetsDef: str
    cleanSheetsGK: str
    shotSuccessRate: str
    passesMade: str
    passSuccessRate: str
    ratingAve: str
    tacklesMade: str
    tackleSuccessRate: str
    proName: str
    proPos: str
    proStyle: str
    proHeight: str
    proNationality: str
    proOverall: str
    manOfTheMatch: str
    redCards: str
    prevGoals: str
    prevGoals1: str
    prevGoals2: str
    prevGoals3: str
    prevGoals4: str
    prevGoals5: str
    prevGoals6: str
    prevGoals7: str
    prevGoals8: str
    prevGoals9: str
    prevGoals10: str
    favoritePosition: str

class MemberStatsPositionCount(BaseModel):
    midfielder: int
    goalkeeper: int
    forward: int
    defender: int

class MemberStats(BaseModel):
    members: List[MemberStatsMember]
    positionCount: MemberStatsPositionCount

class MatchClubsDetails(BaseModel):
    name: str
    clubId: int
    regionId: int
    teamId: int
    customKit: CustomKit

class MatchClubsData(BaseModel):
    date: str
    gameNumber: str
    goals: str
    goalsAgainst: str
    losses: str
    matchType: str
    result: str
    score: str
    season_id: str
    TEAM: str
    ties: str
    winnerByDnf: str
    wins: str
    details: Optional[MatchClubsDetails] = None  # Updated to be optional


class MatchTimeAgo(BaseModel):
    number: int
    unit: str

class MatchPlayersStats(BaseModel):
    assists: str
    cleansheetsany: str
    cleansheetsdef: str
    cleansheetsgk: str
    goals: str
    goalsconceded: str
    losses: str
    mom: str
    namespace: str
    passattempts: str
    passesmade: str
    pos: str
    rating: str
    realtimegame: str
    realtimeidle: str
    redcards: str
    saves: str
    SCORE: str
    shots: str
    tackleattempts: str
    tacklesmade: str
    vproattr: str
    vprohackreason: str
    wins: str
    playername: str

class MatchAggregateStats(BaseModel):
    assists: int
    cleansheetsany: int
    cleansheetsdef: int
    cleansheetsgk: int
    goals: int
    goalsconceded: int
    losses: int
    mom: int
    namespace: int
    passattempts: int
    passesmade: int
    pos: int
    rating: float
    realtimegame: int
    realtimeidle: int
    redcards: int
    saves: int
    SCORE: int
    shots: int
    tackleattempts: int
    tacklesmade: int
    vproattr: int
    vprohackreason: int
    wins: int

class Match(BaseModel):
    matchId: str
    timestamp: int
    timeAgo: MatchTimeAgo
    clubs: Dict[str, MatchClubsData]
    players: Dict[str, Dict[str, MatchPlayersStats]]
    aggregate: Dict[str, MatchAggregateStats]
