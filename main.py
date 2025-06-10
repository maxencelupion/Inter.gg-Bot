import os
import discord
from discord.ext import commands
from load_env import TOKEN


class MyBot(commands.Bot):
	def __init__(self):
		super().__init__(command_prefix='$', intents=discord.Intents.all())

	async def setup_hook(self):
		cogs_dir = os.path.join(os.path.dirname(__file__), "src", "cogs")
		for file in os.listdir(cogs_dir):
			if file.endswith(".py") and not file.startswith("__"):
				extension_name = f"src.cogs.{file[:-3]}"
				await bot.load_extension(extension_name)

bot = MyBot()

bot.run(TOKEN)
