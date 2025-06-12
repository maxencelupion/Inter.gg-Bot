import os
import discord
from src.lol import *
from discord.ext import commands, tasks
from discord import app_commands
from src.database.database import Database
from src.models.models import Server, Account

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
        self.session = self.database.get_session()

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

    @app_commands.command(name="link_bot", description="Link the Inter.gg Bot to a channel.")
    @discord.app_commands.describe(channel="Discord channel to link the bot")
    async def link_bot_to_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """
        Link the bot to the given channel to use for the server interaction. Add it to the DB.
        :param interaction: Discord interaction
        :param channel: Discord channel to use
        """
        await interaction.response.defer()
        try:
            # Remove all inactive servers ? > 3 month ?
            count = self.session.query(Server).count()

            if (count >= 200):
                print(f"Error linking Inter.gg Bot to {channel.mention} channel, max server amount reached.")
                await interaction.followup.send(
                    content="The bot is already linked to 200 servers. Please contact the developer to link more.",
                    ephemeral=True
                )
                return

            existing_server = self.session.query(Server).filter_by(server_id=interaction.guild_id).first()
            if existing_server:
                existing_server.channel_id = channel.id
            else:
                new_server = Server(server_id=interaction.guild_id, channel_id=channel.id)
                self.session.add(new_server)

            self.session.commit()

            await interaction.followup.send(
                content=f"Inter.gg Bot will now use the {channel.mention} channel.",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error linking Inter.gg Bot to {channel.mention} channel, {e}.")
            await interaction.followup.send(f"Error linking Inter.gg Bot to {channel.mention} channel.")

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
        await interaction.response.defer(ephemeral=True)
        tag = tag.replace("#", "").upper()

        try:
            existing_server = self.session.query(Server).filter_by(server_id=interaction.guild_id).first()

            if not existing_server:
                print(f"Error adding account {pseudo}#{tag}, no channel linked.")
                await interaction.followup.send(
                    content="To start tracking account, you first need to link the bot to a channel.",
                    ephemeral=True
                )
                return

            count = self.session.query(Account).count()

            if count >= 200:
                print(f"Error adding account {pseudo}#{tag}, max accounts amount reached.")
                await interaction.followup.send(
                    content="The bot is already tracking 200 accounts. Please contact the developer to track more.",
                    ephemeral=True
                )
                return

            existing_account = self.session.query(Account).filter(
                (Account.riot_username == pseudo) & (Account.user_tag == tag)
            ).first()

            if existing_account:
                await interaction.followup.send(
                    f"Account {pseudo}#{tag} is already tracked.",
                    ephemeral=True
                )
                return

            encrypted_id = await store_ids(pseudo, tag)

            if not encrypted_id:
                print('account invalid')
                await interaction.followup.send(
                    f"Account {pseudo}#{tag} does not exist or is invalid.",
                    ephemeral=True
                )
                return

            new_account = Account(
                riot_username=pseudo,
                user_tag=tag,
                encrypted_id=encrypted_id,
                discord_user=str(interaction.user.id),
                server=existing_server
            )
            print('new account created')
            self.session.add(new_account)
            self.session.commit()

            await interaction.followup.send(
                f"Account {pseudo}#{tag} successfully added.",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(
                f"Error adding account {pseudo}#{tag}.",
                ephemeral=True
            )
            print(f"Exception: {e}")

    @tasks.loop(seconds=60.0)
    async def check_in_game(self):
        """
        This task is called every 60 seconds.
        Check every user if they're currently in game or not, and compare it to their previous state.
        Send a message in the channel of the server if it game just started or if he just finished
        a game. The message contains some information about the game -> queue, champion, Porofessor game url.
        """
        global champ_dict
        accounts = self.session.query(Account).all()
        for account in accounts:
            was_in_game = account.in_game
            is_in_game = True # Check
            if (not was_in_game and is_in_game):
            # Game just started
                account.in_game = True
                return 'Game started'
            if (was_in_game and not is_in_game):
            # Game just finished
                account.in_game = False
                return 'Game finished'

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
                print(e)
                await interaction.followup.send(f"Error reloading {cog}.")

async def setup(bot):
    await bot.add_cog(Greetings(bot))
