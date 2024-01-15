import os
from dotenv import load_dotenv

load_dotenv()

TOKEN: str = os.getenv('DISCORD_TOKEN')
LOL_API_KEY: str = os.getenv("LOL_API_KEY")
HOST_DB: str = os.getenv("HOST_DB")
USER_DB: str = os.getenv("USER_DB")
PASSWORD_DB: str = os.getenv("PASSWORD_DB")
PORT_DB: str = os.getenv("PORT_DB")