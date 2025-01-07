from pydantic import BaseModel, Field, constr
from enum import Enum
from typing import Literal

from .platform import Platform

class MatchType(str, Enum):
    LEAGUE_MATCH = 'leagueMatch'
    PLAYOFF_MATCH = 'playoffMatch'


# -- Input Schemas --

class ClubSearchInput(BaseModel):
    clubName: constr(min_length=1, max_length=32)
    platform: Platform


class OverallStatsInput(BaseModel):
    clubIds: str = Field(..., description="Comma-separated list of club IDs")
    platform: Platform


class MemberCareerStatsInput(BaseModel):
    clubId: str
    platform: Platform


class MemberStatsInput(BaseModel):
    clubId: str
    platform: Platform


class MatchesStatsInput(BaseModel):
    clubIds: str
    platform: Platform
    matchType: MatchType


class ClubInfoInput(BaseModel):
    clubIds: str
    platform: Platform


SCHEMAS = {
    "CLUB_SEARCH": ClubSearchInput,
    "OVERALL_STATS": OverallStatsInput,
    "MEMBER_CAREER_STATS": MemberCareerStatsInput,
    "MEMBER_STATS": MemberStatsInput,
    "MATCHES_STATS": MatchesStatsInput,
    "CLUB_INFO": ClubInfoInput,
}
