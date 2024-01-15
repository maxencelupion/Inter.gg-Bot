FROM python:3.11.6

WORKDIR /app/discord_bot/Inter.gg-BOT
COPY . .
RUN ["pip3", "install", "-r", "requirements.txt"]

ENTRYPOINT ["python3", "main.py"]