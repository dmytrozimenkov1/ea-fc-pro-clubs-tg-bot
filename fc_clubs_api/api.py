# fc_clubs_api/api.py

import requests
from typing import Any, TypeVar, Type, Generic, List
from urllib.parse import urljoin
from enum import Enum  # Import Enum
from .routes import ROUTES, TRouteName
from pydantic import BaseModel
from .models import (
    Club,
    ClubInfo,
    OverallStats,
    MemberCareerStats,
    MemberStats,
    Match,
)

TInput = TypeVar("TInput", bound=BaseModel)


class EAFCApiService:
    def __init__(self, base_url: str = "https://proclubs.ea.com/api/fc/"):
        # Ensure base_url ends with a slash for urljoin
        if not base_url.endswith("/"):
            base_url += "/"
        self.base_url = base_url

        # Define default headers
        self.default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) "
                "Gecko/20100101 Firefox/112.0"
            ),
            "Accept": "application/json",
        }

    def _get(
        self,
        route_name: TRouteName,
        input_data: BaseModel,
        response_model: Type[BaseModel] = None
    ) -> Any:
        """
        Internal method to perform GET requests.
        Validates input, constructs the URL, and returns the parsed JSON as a Pydantic model if provided.
        """
        # Retrieve route configuration
        route_config = ROUTES[route_name]

        # Construct the full URL
        full_url = urljoin(self.base_url, route_config.url)

        # Convert input data to query parameters
        params = {
            k: (v.value if isinstance(v, Enum) else str(v))
            for k, v in input_data.dict().items()
            if v is not None
        }

        # Debugging: Print the constructed URL and params
        print(f"Request URL: {full_url}")
        print(f"Query Parameters: {params}")

        # Send the GET request
        response = requests.get(full_url, headers=self.default_headers, params=params)
        response.raise_for_status()  # Raise an error for 4xx/5xx responses

        # Parse the response JSON
        json_data = response.json()

        # If a response model is provided, parse the JSON into the model
        if response_model:
            if issubclass(response_model, BaseModel):
                return response_model.parse_obj(json_data)
            else:
                return response_model(json_data)
        else:
            return json_data

    # -- Public methods that mirror the TS code: --

    def search_club(self, input_data: BaseModel) -> List[Club]:
        """
        Search for a club by name.
        Returns a list of Club objects.
        """
        raw_response = self._get("CLUB_SEARCH", input_data)
        return [Club(**club_dict) for club_dict in raw_response]

    def overall_stats(self, input_data: BaseModel) -> List[OverallStats]:
        """
        Get overall stats of the club.
        Returns a list of OverallStats objects.
        """
        raw_response = self._get("OVERALL_STATS", input_data)
        return [OverallStats(**stat_dict) for stat_dict in raw_response]

    def member_career_stats(self, input_data: BaseModel) -> MemberCareerStats:
        """
        Get the career stats of all members of the club.
        """
        raw_response = self._get("MEMBER_CAREER_STATS", input_data)
        return MemberCareerStats.parse_obj(raw_response)

    def member_stats(self, input_data: BaseModel) -> MemberStats:
        """
        Get the stats of all members of the club.
        """
        raw_response = self._get("MEMBER_STATS", input_data)
        return MemberStats.parse_obj(raw_response)

    def matches_stats(self, input_data: BaseModel) -> List[Match]:
        """
        Get the stats of all matches of the club.
        """
        raw_response = self._get("MATCHES_STATS", input_data)
        return [Match(**match_dict) for match_dict in raw_response]

    def club_info(self, input_data: BaseModel) -> ClubInfo:
        """
        Gets information of a club.
        The response is keyed by `clubId`.
        """
        raw_response = self._get("CLUB_INFO", input_data)
        return ClubInfo.parse_obj(raw_response)
