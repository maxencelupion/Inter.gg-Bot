import json
import pandas as pd
import aiohttp
import requests
import sys

from load_env import LOL_API_KEY

base_url = "https://euw1.api.riotgames.com"
second_base_url = "https://europe.api.riotgames.com"
api_key = "?api_key=" + LOL_API_KEY


class Account:
	"""
	Account class
	"""
	def __init__(self, username, tag):
		self.id = None
		self.encrypted_id = None
		self.games = []
		self.username = username
		self.tag = tag

	async def get_id(self):
		"""
		Get the id and encrypted id of the account
		"""
		method_pseudo = "/riot/account/v1/accounts/by-riot-id/"
		url_pseudo = second_base_url + method_pseudo + self.username + "/" + self.tag + api_key
		method_pseudo_2 = "/lol/summoner/v4/summoners/by-puuid/"
		async with aiohttp.ClientSession() as session:
			async with session.get(url_pseudo) as response:
				api_response_text = await response.text()
				api_response_json = json.loads(api_response_text)
				self.id = api_response_json["puuid"]
			url_pseudo_2 = base_url + method_pseudo_2 + self.id + api_key
			async with session.get(url_pseudo_2) as response:
				api_response_text = await response.text()
				api_response_json = json.loads(api_response_text)
				self.encrypted_id = api_response_json["id"]


async def get_x_last_games(id_acc, x):
	method_match = f"/lol/match/v5/matches/by-puuid/{id_acc}/ids" + "?start=0&count=" + str(
		x) + "&api_key=" + LOL_API_KEY
	url_match = second_base_url + method_match
	async with aiohttp.ClientSession() as session:
		async with session.get(url_match) as response:
			api_response_text = await response.text()
	return json.loads(api_response_text)


async def get_match_data(account):
	method_data_match = "/lol/match/v5/matches/"
	win = 0
	result = ["", "", "", "", ""]
	async with aiohttp.ClientSession() as session:
		for id_match in account.games:
			url_data_match = second_base_url + method_data_match + id_match + api_key
			async with session.get(url_data_match) as response:
				api_response_text = await response.text()
				api_response_json = json.loads(api_response_text)
				participants_list = api_response_json["metadata"]["participants"]
				for index, participant in enumerate(participants_list):
					if participant == account.id:
						position = index
				df = pd.DataFrame(api_response_json["info"]["participants"])
				if df["win"][position]:
					win += 1
	result[0] = win
	result[1] = len(account.games) - win
	result[2] = result[0] / len(account.games) * 100
	result[3] = account.username
	result[4] = len(account.games)
	return result


async def is_in_game(account):
	"""
	Check if the account is in game.
	:param account: account class referring a LoL account
	:return response:
	"""
	method_spectator = '/lol/spectator/v5/active-games/by-summoner/'
	url_spectator = base_url + method_spectator + account.id + api_key
	try:
		return requests.get(url_spectator)
	except Exception as e:
		print(e)


async def get_last_game(account):
	"""
	Get the last game of the account. This function is called after is_in_game if the account is no longer in game.
	:param account: account class referring a LoL account
	:return response:
	"""
	method_match = f"/lol/match/v5/matches/by-puuid/{account.id}/ids" + "?start=0&count=1" + "&api_key=" + LOL_API_KEY
	url_match = second_base_url + method_match
	response = requests.get(url_match)
	api_response_text = response.text
	id_last_game = json.loads(api_response_text)[0]
	url_data_match = second_base_url + "/lol/match/v5/matches/" + id_last_game + api_key
	try:
		return requests.get(url_data_match)
	except Exception as e:
		print(e)


async def test_lol_by_puuid(puuid):
	"""
	Test if the pseudo is associated to an existing LoL account in EUW region
	:param puuid: puuid of the riot account. Must be a str.
	:return bool:
	"""
	method_puuid = "/lol/summoner/v4/summoners/by-puuid/"
	url_puuid = base_url + method_puuid + puuid + api_key
	async with aiohttp.ClientSession() as session:
		async with session.get(url_puuid) as response:
			if response.status != 200:
				return False
			else:
				return True


async def get_league_points(pseudo, tag, queue):
	"""
	Get the league points of the account for a given queue. This function is called if the account is no longer in game.
	:param pseudo: pseudo of the account. Must be a str.
	:param queue: queue of the account. Must be an int.
	:return int:
	"""
	method_league_points = "/lol/league/v4/entries/by-summoner/"
	acc = Account(pseudo, tag)
	await acc.get_id()
	url_league_points = base_url + method_league_points + str(acc.encrypted_id) + api_key
	async with aiohttp.ClientSession() as session:
		async with session.get(url_league_points) as response:
			api_response_text = await response.text()
			api_response_json = json.loads(api_response_text)
			for i in range(len(api_response_json)):
				if queue == 0 and api_response_json[i]["queueType"] == "RANKED_FLEX_SR":
					return int(api_response_json[i]["leaguePoints"])
				elif queue == 2 and api_response_json[i]["queueType"] == "RANKED_SOLO_5x5":
					return int(api_response_json[i]["leaguePoints"])
			return 0


async def get_division(pseudo, tag, queue):
	"""
	Get the division of the account for a given queue. This function is called when the account is added to the DB or when
	the account is no longer in game.
	:param pseudo: pseudo of the account. Must be a str.
	:param queue: queue of the account. Must be an int.
	:return str:
	"""
	method_league_points = "/lol/league/v4/entries/by-summoner/"
	acc = Account(pseudo, tag)
	await acc.get_id()
	url_league_points = base_url + method_league_points + str(acc.encrypted_id) + api_key
	async with aiohttp.ClientSession() as session:
		async with session.get(url_league_points) as response:
			api_response_text = await response.text()
			api_response_json = json.loads(api_response_text)
			for i in range(len(api_response_json)):
				if queue == 0 and api_response_json[i]["queueType"] == "RANKED_FLEX_SR":
					return api_response_json[i]["tier"]
				if queue == 2 and api_response_json[i]["queueType"] == "RANKED_SOLO_5x5":
					return api_response_json[i]["tier"]
			return "Unranked"


async def get_tier(pseudo, tag, queue):
	"""
	Get the tier of the account for a given queue. This function is called when the account is added to the DB or when
	the account is no longer in game.
	:param pseudo: pseudo of the account. Must be a str.
	:param queue: queue of the account. Must be an int.
	:return str:
	"""
	method_league_points = "/lol/league/v4/entries/by-summoner/"
	acc = Account(pseudo, tag)
	await acc.get_id()
	url_league_points = base_url + method_league_points + str(acc.encrypted_id) + api_key
	async with aiohttp.ClientSession() as session:
		async with session.get(url_league_points) as response:
			api_response_text = await response.text()
			api_response_json = json.loads(api_response_text)
			for i in range(len(api_response_json)):
				if queue == 0 and api_response_json[i]["queueType"] == "RANKED_FLEX_SR":
					return api_response_json[i]["rank"]
				elif queue == 2 and api_response_json[i]["queueType"] == "RANKED_SOLO_5x5":
					return api_response_json[i]["rank"]
			return "IV"


async def test_riot_acc(pseudo, tag):
	"""
	Test if the pseudo is associated to an existing LoL account in EUW region
	:param pseudo: pseudo of the account. Must be a str.
	:param tag: tag of the account. Must be a str.
	:return bool:
	"""
	method_pseudo = "/riot/account/v1/accounts/by-riot-id/"
	url_pseudo = second_base_url + method_pseudo + pseudo.replace(" ", "%20") + "/" + tag + api_key
	async with aiohttp.ClientSession() as session:
		async with session.get(url_pseudo) as response:
			if response.status != 200:
				return
			else:
				api_response_text = await response.text()
				api_response_json = json.loads(api_response_text)
				return api_response_json["puuid"]


