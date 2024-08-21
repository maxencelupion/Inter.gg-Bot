import json
import sys
import discord
import os
import asyncio
from database.db import *
from lol import *
from get_champ_dict import get_latest_ddragon, get_champion_by_key, get_champ_icon
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime

dict_queue_id = {420: "solo", 440: "flex"}
dict_queue = {"solo": 2, "flex": 0}
colors = {"blue": 0x50749b, "green": 0x1a994a, "red": 0xab0303, "yellow": 0xc49c2d}
tiers = {"I": 4, "II": 3, "III": 2, "IV": 1}
divisions = {"Unranked": 0, "IRON": 1, "BRONZE": 2, "SILVER": 3, "GOLD": 4, "PLATINUM": 5, "EMERALD": 6, "DIAMOND": 7, "MASTER": 8, "GRANDMASTER": 9, "CHALLENGER": 10}
champ_dict = {}
COGS = []
for file in os.listdir("cogs"):
	if file.endswith(".py"):
		COGS.append(file[:-3])


class Greetings(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_ready(self):
		print(f'Connecté en tant que {self.bot.user.name}')
		try:
			synced = await self.bot.tree.sync()
			print(f"Synced {len(synced)} commands")
			for command in synced:
				print(f"Synced {command.name}")
			global champ_dict
			champ_dict = await get_latest_ddragon()
			while not champ_dict:
				await asyncio.sleep(1)
			if not self.check_in_game.is_running():
				self.check_in_game.start()
		except Exception as e:
			print(e)

	@app_commands.command(name="get_started", description="Get started guide to start using the Inter.gg Bot !")
	async def get_started(self, interaction: discord.Interaction):
		"""
		Display the get started message.
		:param interaction: Discord interaction
		"""
		await interaction.response.defer()
		embed = discord.Embed(
			title="**Get Started !** ",
			description="To start using the bot, you first need to assign a channel for it to use with the command /init_bot:"
			"```/init_bot {channel}```"
			"**Note that you can change the selected channel at any time by using the /init_bot command again**\n\n"
			"You can then add a Riot account to follow! **Note: these accounts must be from the EUW region.**\n"
			"```/add_account {Riot account name}{Riot account tag}```\n"
			"You can also delete these accounts in the same way.\n"
			"```/delete_account {Riot account name}{Riot account tag}```\n"
			"_Made by https://github.com/maxencelupion_",
			colour=colors["yellow"],
			timestamp=datetime.now()
		)
		embed.set_author(name="Inter.gg Bot")
		embed.set_footer(text="Get Started Guide")
		await interaction.followup.send(embed=embed)

	@app_commands.command(name="init_bot", description="Init the Inter.gg Bot to a channel.")
	@discord.app_commands.describe(channel="Discord channel to init the bot")
	async def init_bot(self, interaction: discord.Interaction, channel: discord.TextChannel):
		"""
		Init the bot to use the given channel for the server interaction. Add it to the DB.
		:param interaction: Discord interaction
		:param channel: Discord channel to use
		"""
		await interaction.response.defer()
		guild_id = interaction.guild_id
		add_server_db(guild_id, channel.id)
		await interaction.followup.send(
			content=f"Inter.gg Bot will now use the {channel.mention} channel.",
			ephemeral=True
		)

	@app_commands.command(name="add_account", description="Add an EUW Riot account to the bot !")
	@discord.app_commands.describe(pseudo="Pseudo of the Riot account to add", tag="Tag of the Riot account to add")
	async def add_account(self, interaction: discord.Interaction, pseudo: str, tag: str):
		"""
		Add a Riot account to the DB and reply to the request on the right channel of the server interaction.
		:param interaction:
		:param pseudo:
		:param tag:
		:return:
		"""
		await interaction.response.defer()
		guild_id = interaction.guild_id
		discord_user = interaction.user
		tag_cleaned = tag.replace("#", "").upper()
		puuid_to_test = await test_riot_acc(pseudo, tag_cleaned)
		if not puuid_to_test:
			await interaction.followup.send(
				content=f"Error while adding the account: the Riot account **_{pseudo}#{tag_cleaned}_** doesn't exists.",
				ephemeral=True
			)
			return
		if not await test_lol_by_puuid(puuid_to_test):
			await interaction.followup.send(
				content=f"Error while adding the account: the LoL account **_{pseudo}#{tag_cleaned}_** doesn't exists.",
				ephemeral=True
			)
			return

		if get_user_by_encrypted_id(puuid_to_test, guild_id) is not None:
			await interaction.followup.send(
				content=f"Error while adding the account: the Riot account **_{pseudo}#{tag_cleaned}_** has already been added.",
				ephemeral=True
			)
			return
		response = add_user_db(pseudo, tag_cleaned, puuid_to_test, discord_user.name, guild_id)
		if "foreign key constraint fails" in str(response):
			await interaction.followup.send(
				content=f"Error while adding the account: Inter.gg Bot must be init to a channel.",
				ephemeral=True
			)
		else:
			lp_flex = await get_league_points(pseudo, tag_cleaned, dict_queue["flex"])
			update_league_points(pseudo, tag_cleaned, lp_flex, dict_queue["flex"])

			lp_solo = await get_league_points(pseudo, tag_cleaned, dict_queue["solo"])
			update_league_points(pseudo, tag_cleaned, lp_solo, dict_queue["solo"])

			division_flex = await get_division(pseudo, tag_cleaned, dict_queue["flex"])
			tier_flex = await get_tier(pseudo, tag_cleaned, dict_queue["flex"])
			update_division_tier(pseudo, tag_cleaned, division_flex, tier_flex, dict_queue["flex"])

			division_solo = await get_division(pseudo, tag_cleaned, dict_queue["solo"])
			tier_solo = await get_tier(pseudo, tag_cleaned, dict_queue["solo"])
			update_division_tier(pseudo, tag_cleaned, division_solo, tier_solo, dict_queue["solo"])


			await interaction.followup.send(
				content=response,
				ephemeral=True
			)

	@discord.app_commands.command(name="remove_account", description="Remove a Riot account")
	@discord.app_commands.describe(pseudo="Pseudo of the Riot account to remove", tag="Tag of the Riot account to add")
	async def remove_account(self, interaction: discord.Interaction, pseudo: str, tag: str):
		"""
		Remove a Riot account from the DB and reply to the request on the right channel of the server interaction.
		:param tag:
		:param interaction: Discord interaction
		:param pseudo: Pseudo of the account to delete given by the user
		"""
		await interaction.response.defer()
		tag_cleaned = tag.replace("#", "").upper()
		guild_id = interaction.guild_id
		response = delete_user_db(pseudo, tag_cleaned, guild_id)
		await interaction.followup.send(
			content=response,
			ephemeral=True
		)

	async def check_in_game_user(self, pseudo, tag, id_channel, old_is_in_game):
		try:
			acc = Account(pseudo, tag)
			await acc.get_id()
			response = await is_in_game(acc)
			api_response_text = response.text
			api_response_json = json.loads(api_response_text)
			champion_id = 0
			if response.status_code == 200 and old_is_in_game == 0:
				queue_id = api_response_json["gameQueueConfigId"]
				if queue_id != 420 and queue_id != 440:
					return
				for participant in api_response_json['participants']:
					if participant['puuid'] == acc.id:
						champion_id = participant['championId']
				data = get_champion_by_key(str(champion_id), champ_dict)
				user_link = pseudo.replace(" ", "+")
				embed = discord.Embed(
					title="Game started",
					description=f"Player **_{pseudo}#{tag}_** is now in game.\n\n",
					colour=colors["blue"],
					timestamp=datetime.now()
				)
				embed.add_field(
					name="Game link",
					value=f"https://porofessor.gg/fr/live/euw/{user_link}-{tag}",
					inline=False
				)
				embed.add_field(
					name="Champion",
					value=f"{data['name']}",
					inline=True
				)
				embed.add_field(
					name="Queue",
					value=f"{dict_queue_id[queue_id].capitalize()}",
					inline=True
				)
				embed.set_author(name="Inter.gg Bot")
				embed.set_thumbnail(url=get_champ_icon(str(champion_id), champ_dict))
				embed.set_footer(text="Info Inter.gg Bot")
				update_user_in_game(pseudo, tag, 1)
				await self.bot.get_channel(id_channel).send(embed=embed)

			elif response.status_code != 200 and old_is_in_game == 1:
				last_game = await get_last_game(acc)
				last_game_text = last_game.text
				api_response_json = json.loads(last_game_text)
				queue_id = api_response_json["info"]["queueId"]
				if queue_id != 420 and queue_id != 440:
					update_user_in_game(pseudo, tag, 0)
					return
				participants_list = api_response_json["metadata"]["participants"]
				game_id = str(api_response_json['metadata']['matchId'])
				game_id = game_id.replace("EUW1_", "")
				position = 0
				for index, participant in enumerate(participants_list):
					if participant == acc.id:
						position = index

				participants_info = api_response_json["info"]["participants"]

				champion_id = participants_info[position]["championId"]
				player_kill = participants_info[position]["kills"]
				player_death = participants_info[position]["deaths"]
				player_assist = participants_info[position]["assists"]

				data_participants = api_response_json["info"]["participants"]
				data = get_champion_by_key(str(data_participants[position]['championId']), champ_dict)

				old_lp = get_last_league_points(pseudo, tag, dict_queue[dict_queue_id[queue_id]])[0]
				old_division = get_last_division(pseudo, tag, dict_queue[dict_queue_id[queue_id]])[0]
				old_tier = get_last_tier(pseudo, tag, dict_queue[dict_queue_id[queue_id]])[0]

				actual_lp = await get_league_points(pseudo, tag, dict_queue[dict_queue_id[queue_id]])
				actual_division = await get_division(pseudo, tag, dict_queue[dict_queue_id[queue_id]])
				actual_tier = await get_tier(pseudo, tag, dict_queue[dict_queue_id[queue_id]])

				update_division_tier(pseudo, tag, actual_division, actual_tier, dict_queue[dict_queue_id[queue_id]])
				update_league_points(pseudo, tag, actual_lp, dict_queue[dict_queue_id[queue_id]])
				if data_participants[position]['win']:
					change = actual_lp - old_lp
					embed = discord.Embed(
						title="Game won",
						description=f"Player **_{pseudo}#{tag}_** just won his game.\n",
						colour=colors["green"],
						timestamp=datetime.now()
					)
					if (tiers[actual_tier] > tiers[old_tier] or divisions[actual_division] > divisions[old_division]):
						embed.add_field(
							name="Promoted",
							value=f"**Ranked up {actual_division}-{actual_tier}** with {actual_lp} LPs, GG !",
							inline=False
						)
					else:
						embed.add_field(
							name="New rank",
							value=f"**+{change} LPs** and is now {actual_division}-{actual_tier} with {actual_lp} LPs.",
							inline=False
						)
				else:
					change = old_lp - actual_lp
					embed = discord.Embed(
						title="Game lost",
						description=f"Player **_{pseudo}#{tag}_** just lost his game.\n",
						colour=colors["red"],
						timestamp=datetime.now()
					)
					if tiers[actual_tier] < tiers[old_tier] or divisions[actual_division] < divisions[old_division]:
						embed.add_field(
							name="Demoted",
							value=f"**Retrograded {actual_division}-{actual_tier}** with {actual_lp} LPs, sad..",
							inline=False
						)
					else:
						embed.add_field(
							name="New rank",
							value=f"**-{change} LPs** and is now {actual_division}-{actual_tier} with {actual_lp} LPs.",
							inline=False
						)
				embed.add_field(
					name="Champion",
					value=f"{data['name']}",
					inline=True
				)
				embed.add_field(
					name="Queue",
					value=f"{dict_queue_id[queue_id].capitalize()}",
					inline=True
				)
				embed.add_field(
					name="KDA",
					value=f"{player_kill}/{player_death}/{player_assist}",
					inline=True
				)
				embed.add_field(
					name="Game link",
					value=f"https://www.leagueofgraphs.com/fr/match/euw/{game_id}",
					inline=True
				)
				embed.set_author(name="Inter.gg Bot")
				embed.set_footer(text="Info Inter.gg Bot")
				embed.set_thumbnail(url=get_champ_icon(str(champion_id), champ_dict))
				update_user_in_game(str(pseudo), str(tag), 0)
				await self.bot.get_channel(id_channel).send(embed=embed)
		except Exception as e:
			print("Exception during task :")
			print(e)

	@tasks.loop(seconds=60.0)
	async def check_in_game(self):
		"""
		This task is called every 60 seconds.
		Check if the user is in game and send a message in the channel of the server if he is in game or if he just finished
		a game. The message contains some information about the game.
		"""
		global champ_dict
		users = get_all_user()
		if users is not None:
			for user in users:
				pseudo = str(user[0])
				tag = str(user[1])
				id_channel = get_channel_by_server(user[4])
				old_is_in_game = user[5]
				await self.check_in_game_user(pseudo, tag, id_channel, old_is_in_game)

	@discord.app_commands.command(name="show_accounts", description="Show all accounts of the server")
	async def show_accounts(self, interaction: discord.Interaction):
		"""
		Show all accounts of the server
		:param interaction:
		:return:
		"""
		await interaction.response.defer()
		server_id = interaction.guild_id
		users = get_all_user_server(server_id)
		if not users:
			await interaction.followup.send(
				content="No account added for your server.",
				ephemeral=False
			)
		else:
			id_channel = get_channel_by_server(server_id)
			embed = discord.Embed(
				title="Users in your server",
				description=f"**{len(users)} in your server:**\n",
				colour=colors["blue"],
				timestamp=datetime.now()
			)
			for user in users:
				pseudo = user[0]
				tag = user[1]
				solo = user[6] + "-" + user[7] + f" with {user[8]} LPs."
				flex = user[9] + "-" + user[10] + f" with {user[11]} LPs."
				embed.add_field(
					name=f"**{pseudo}#{tag}**",
					value=f"Solo: {solo} - Flex: {flex}",
					inline=False
				)
			embed.set_author(name="Inter.gg Bot")
			embed.set_footer(text="Info Inter.gg Bot")
			await interaction.followup.send(
				content="Here are the accounts of your server:",
				ephemeral=True
			)
			await self.bot.get_channel(id_channel).send(embed=embed)

	@discord.app_commands.command(name="reload_cogs", description="Reload all cogs")
	@discord.app_commands.checks.has_permissions(administrator=True)
	async def reload_cogs(self, ctx: discord.Interaction) -> None:
		"""
		Reload all cogs
		:param ctx:
		:return:
		"""
		await ctx.response.defer(ephemeral=True)
		for cog in COGS:
			try:
				await self.bot.reload_extension(f"cogs.{cog}")
				await ctx.followup.send(f"{cog} reloaded")
			except Exception as e:
				await ctx.followup.send(f"Error: {e}")

	@discord.app_commands.command(name="restart_task_check_in_game", description="Restarts task check_in_game")
	@discord.app_commands.checks.has_permissions(administrator=True)
	async def restart_task(self, ctx: discord.Interaction) -> None:
		"""
		Restarts task check_in_game
		"""
		await ctx.response.defer(ephemeral=True)
		if self.check_in_game.is_running():
			self.check_in_game.restart()
		else:
			self.check_in_game.start()
		await ctx.followup.send("Task restarted")


async def setup(bot):
	await bot.add_cog(Greetings(bot))
