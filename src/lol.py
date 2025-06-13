import aiohttp
import json
from load_env import LOL_API_KEY

LOL_BASE_URL = "https://euw1.api.riotgames.com"
RIOT_BASE_URL = "https://europe.api.riotgames.com"
API_KEY_QUERY_PARAM = "?api_key=" + LOL_API_KEY

async def get_puuid(riot_username: str, user_tag: str):
    """
    Get the PUUID of a Riot account using the Riot username and user tag.
    :param riot_username: Riot username
    :param user_tag: Riot user tag
    """
    account_url = f"{RIOT_BASE_URL}/riot/account/v1/accounts/by-riot-id/{riot_username}/{user_tag}{API_KEY_QUERY_PARAM}"
    async with aiohttp.ClientSession() as session:
        async with session.get(account_url) as response:
            if (response.status != 200):
                print(f"Riot API responded with {response.status} for Riot username: {riot_username} and tag: {user_tag}")
                return None

            try:
                data = await response.json()
            except Exception as e:
                print(f"Failed to parse JSON response: {e}")
                return None

            return data["puuid"] # return the puuid, if the account exists

async def get_tier(puuid: str, flex_queue: bool = False):
    """
    Get the tier of a Riot account using the PUUID.
    :param puuid: PUUID of the Riot account
    :param flex_queue: True to fetch Flex queue points, False for Solo queue.
    """
    tier_url = f"{LOL_BASE_URL}/lol/league/v4/entries/by-puuid/{puuid}{API_KEY_QUERY_PARAM}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(tier_url) as response:
                if response.status != 200:
                    print(f"Riot API responded with {response.status} for PUUID: {puuid}")
                    return None

                data = await response.json()

                target_queue = "RANKED_FLEX_SR" if flex_queue else "RANKED_SOLO_5x5"
                for entry in data:
                    if entry.get("queueType") == target_queue:
                        return entry.get("tier", "UNRANKED")

                return "UNRANKED"

    except Exception as e:
        print(f"Failed to fetch tier: {e}")
        return None

async def get_rank(puuid: str, flex_queue: bool = False):
    """
    Get the rank of a Riot account using the PUUID.
    :param puuid: PUUID of the Riot account
    :param flex_queue: True to fetch Flex queue points, False for Solo queue.
    """
    rank_url = f"{LOL_BASE_URL}/lol/league/v4/entries/by-puuid/{puuid}{API_KEY_QUERY_PARAM}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(rank_url) as response:
                if response.status != 200:
                    print(f"Riot API responded with {response.status} for PUUID: {puuid}")
                    return None

                data = await response.json()

                target_queue = "RANKED_FLEX_SR" if flex_queue else "RANKED_SOLO_5x5"
                for entry in data:
                    if entry.get("queueType") == target_queue:
                        return entry.get("rank", "UNRANKED")

                return "UNRANKED"

    except Exception as e:
        print(f"Failed to fetch rank: {e}")
        return None

async def get_league_points(puuid: str, flex_queue: bool = False):
    """
    Get the league points of a Riot account using the PUUID.
    :param puuid: PUUID of the Riot account
    :param flex_queue: True to fetch Flex queue points, False for Solo queue.
    """
    league_points_url = f"{LOL_BASE_URL}/lol/league/v4/entries/by-puuid/{puuid}{API_KEY_QUERY_PARAM}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(league_points_url) as response:
                if response.status != 200:
                    print(f"Riot API responded with {response.status} for PUUID: {puuid}")
                    return None

                data = await response.json()

                target_queue = "RANKED_FLEX_SR" if flex_queue else "RANKED_SOLO_5x5"
                for entry in data:
                    if entry.get("queueType") == target_queue:
                        return entry.get("leaguePoints", -1)

                return -1

    except Exception as e:
        print(f"Failed to fetch league points: {e}")
        return None
