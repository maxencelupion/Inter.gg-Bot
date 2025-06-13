import os
import discord
import datetime
from src.lol import *
from discord.ext import commands, tasks
from discord import app_commands
from src.database.database import Database
from src.models.models import Server, Account

AUTHOR = {"name": "Inter.gg Bot", "url": "https://github.com/maxencelupion/Inter.gg-Bot"}
COLORS = {"blue": 0x50749b, "green": 0x1a994a, "red": 0xab0303, "yellow": 0xc49c2d}
COGS = []
COGS_DIR = os.path.join(os.path.dirname(__file__), "..", "cogs")
COGS_DIR = os.path.abspath(COGS_DIR)
for file in os.listdir(COGS_DIR):
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

    @app_commands.command(name="get_started", description=f"Get started guide to start using the {AUTHOR['name']} !")
    async def get_started(self, interaction: discord.Interaction):
        """
        Display the get started message.
        :param interaction: Discord interaction
        """
        await interaction.response.defer()
        embed = discord.Embed(
            title="**Get Started !** ",
            description="To start using the bot, you first need to link a channel to be used with the command /init_bot:"
                        "```/link_bot {channel}```"
                        "**Note that you can change the selected channel at any time by using the /link_bot command again**\n\n"
                        "You can then add a Riot account to track ! **Note: these accounts must be from the EUW region.**\n"
                        "```/add_account {Riot account name}{Riot account tag}```\n"
                        "You can also delete these accounts in the same way.\n"
                        "```/delete_account {Riot account name}{Riot account tag}```\n"
                        "_Made by https://github.com/maxencelupion_",
            colour=COLORS["yellow"],
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=AUTHOR['name'], url=AUTHOR['url'])
        embed.set_footer(text="Get Started Guide")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="link_bot", description=f"Link the {AUTHOR['name']} to a channel.")
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
                print(f"Error linking {AUTHOR['name']} to {channel.mention} channel, max server amount reached.")
                await interaction.followup.send(
                    content=f"{AUTHOR['name']} is already linked to 200 servers. Please contact the developer to link more.",
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
                content=f"{AUTHOR['name']} will now use the {channel.mention} channel.",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error linking {AUTHOR['name']} to {channel.mention} channel, {e}.")
            await interaction.followup.send(f"Error linking {AUTHOR['name']} to {channel.mention} channel.")

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
                    content=f"{AUTHOR['name']} is already tracking 200 accounts. Please contact the developer to track more.",
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
