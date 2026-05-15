import os
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}


def api_get(endpoint, params=None):
    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        headers=HEADERS,
        params=params,
        timeout=20
    )

    data = response.json()
    print("API RESPONSE:", data)
    return data


def get_live_upcoming_matches():
    today = date.today()
    future = today + timedelta(days=14)

    data = api_get("fixtures", {
        "league": 39,
        "season": 2025,
        "from": today.isoformat(),
        "to": future.isoformat()
    })

    return data.get("response", [])


def simplify_fixture(fixture):
    return {
        "fixture_id": fixture["fixture"]["id"],
        "date": fixture["fixture"]["date"],
        "league": fixture["league"]["name"],
        "home": fixture["teams"]["home"]["name"],
        "away": fixture["teams"]["away"]["name"],
        "status": fixture["fixture"]["status"]["short"],
    }