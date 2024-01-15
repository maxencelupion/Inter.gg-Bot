import asyncio
import os
import discord
from discord.ext import commands
from load_env import TOKEN


class MyBot(commands.Bot):
	def __init__(self):
		super().__init__(command_prefix='$', intents=discord.Intents.all())

	async def setup_hook(self):
		for filename in os.listdir("./cogs"):
			if filename.endswith(".py"):
				await bot.load_extension(f"cogs.{filename[:-3]}")


bot = MyBot()

bot.run(TOKEN)
