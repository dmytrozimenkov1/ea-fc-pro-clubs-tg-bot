# fc_clubs_api/routes.py

from typing import Dict, Literal, Type
from pydantic import BaseModel, ConfigDict

from .schemas import (
    SCHEMAS,
    ClubSearchInput,
    OverallStatsInput,
    MemberCareerStatsInput,
    MemberStatsInput,
    MatchesStatsInput,
    ClubInfoInput,
)

TRouteName = Literal[
    "CLUB_SEARCH",
    "OVERALL_STATS",
    "MEMBER_CAREER_STATS",
    "MEMBER_STATS",
    "MATCHES_STATS",
    "CLUB_INFO"
]


class RouteConfig(BaseModel):
    """Holds a route's URL and the Pydantic model used to validate input_data."""

    url: str
    input_model: Type[BaseModel]

    # For Pydantic v2:
    model_config = ConfigDict(arbitrary_types_allowed=True)


ROUTES: Dict[TRouteName, RouteConfig] = {
    "CLUB_SEARCH": RouteConfig(
        url="allTimeLeaderboard/search",
        input_model=ClubSearchInput
    ),
    "OVERALL_STATS": RouteConfig(
        url="clubs/overallStats",
        input_model=OverallStatsInput
    ),
    "MEMBER_CAREER_STATS": RouteConfig(
        url="members/career/stats",
        input_model=MemberCareerStatsInput
    ),
    "MEMBER_STATS": RouteConfig(
        url="members/stats",
        input_model=MemberStatsInput
    ),
    "MATCHES_STATS": RouteConfig(
        url="clubs/matches",
        input_model=MatchesStatsInput
    ),
    "CLUB_INFO": RouteConfig(
        url="clubs/info",
        input_model=ClubInfoInput
    ),
}
