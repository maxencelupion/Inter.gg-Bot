import asyncio
import requests

champion_json = {}


async def get_latest_ddragon():
    versions = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
    latest = versions.json()[0]

    ddragon = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{latest}/data/en_US/champion.json")

    champions = ddragon.json()["data"]
    return champions


def get_champion_by_key(key, data_dict):
    for champion_name in data_dict:
        if data_dict[champion_name]["key"] == key:
            return data_dict[champion_name]

    return False


def get_icon_by_key(key, data_dict):
    for champion_name in data_dict:
        if data_dict[champion_name]["key"] == key:
            data = data_dict[champion_name]
            return data["image"]["full"]

    return False


def get_champ_icon(key, data_dict):
    versions = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
    latest = versions.json()[0]
    url = get_icon_by_key(key, data_dict)
    return f"https://ddragon.leagueoflegends.com/cdn/{latest}/img/champion/{str(url)}"
