import aiohttp
import json
from src.models.models import Server, Account
from load_env import LOL_API_KEY

base_url = "https://euw1.api.riotgames.com"
second_base_url = "https://europe.api.riotgames.com"
api_key = "?api_key=" + LOL_API_KEY

async def store_ids(riot_username: str, user_tag: str):
    pseudo_url = "/riot/account/v1/accounts/by-riot-id/"
    url_pseudo = f"{second_base_url}{pseudo_url}{riot_username}/{user_tag}{api_key}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url_pseudo) as response:
            if (response.status != 200):
                return None
            api_response_text = await response.text()
            api_response_json = json.loads(api_response_text)
            return api_response_json["puuid"] # return the puuid, if the account exists