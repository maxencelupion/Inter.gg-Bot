import os
import discord
from discord.ext import commands
from discord import app_commands
from src.database.database import Database
from src.models.models import Server

COGS = []
cogs_dir = os.path.join(os.path.dirname(__file__), "..", "cogs")
cogs_dir = os.path.abspath(cogs_dir)
for file in os.listdir(cogs_dir):
    if file.endswith(".py"):
        COGS.append(file[:-3])

class Greetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = Database()


    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Connected as {self.bot.user.name}')
        try:
            synced = await self.bot.tree.sync()
            print(f"Synced {len(synced)} commands")
            for command in synced:
                print(f"Synced {command.name}")
        except Exception as e:
            print(e)

    @app_commands.command(name="ping", description="Pong !")
    @app_commands.checks.has_permissions(administrator=True)
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Pong!", ephemeral=True)

    @app_commands.command(name="init_bot", description="Link the Inter.gg Bot to a channel.")
    @discord.app_commands.describe(channel="Discord channel to linkthe bot")
    async def link_bot_to_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """
        Link the bot to the given channel to use for the server interaction. Add it to the DB.
        :param interaction: Discord interaction
        :param channel: Discord channel to use
        """
        await interaction.response.defer()
        try:
            guild_id = interaction.guild_id
            session = self.database.get_session()

            existing_server = session.query(Server).filter_by(server_id=guild_id).first()
            if existing_server:
                existing_server.channel_id = channel.id
            else:
                new_server = Server(server_id=guild_id, channel_id=channel.id)
                session.add(new_server)

            session.commit()

            await interaction.followup.send(
                content=f"Inter.gg Bot will now use the {channel.mention} channel.",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error linking Inter.gg Bot to {channel.mention} channel, {e}.")
            await interaction.followup.send(f"Error linking Inter.gg Bot to {channel.mention} channel.")

    @app_commands.command(name="reload_cogs", description="Reload all cogs")
    @app_commands.checks.has_permissions(administrator=True)
    async def reload_cogs(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        for cog in COGS:
            try:
                await self.bot.reload_extension(f"src.cogs.{cog}")
                await interaction.followup.send(f"{cog} reloaded")
                print(f"{cog} reloaded")
            except Exception as e:
                await interaction.followup.send(f"Error reloading {cog}: {e}")

async def setup(bot):
    await bot.add_cog(Greetings(bot))
