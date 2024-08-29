import sys
import time
from game_tracker.load_env import USER_DB, PASSWORD_DB, HOST_DB, PORT_DB
import mysql.connector


def connector_db():
	"""
	Return a MySQL connector using env variables
	:return mysql.connector:
	"""
	while True:
		try:
			#TO CHANGE
			connection = mysql.connector.connect(
				host="inter_db",
				user="root",
				password="root",
				database="discord_lol"
			)
			if connection.is_connected():
				return connection
		except Exception as e:
			print(f"Error: {e}")
			time.sleep(5)


def add_server_db(server_id, channel_id):
	"""
	Add a server, and it channels to use to the DB
	:param server_id: id of the discord server. Must be a str.
	:param channel_id: id of the channel to use. Must be a str.
	"""
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		my_cursor.execute(f"SELECT * FROM guild_init WHERE server_id='{server_id}';")
		row = my_cursor.fetchone()
		if row is not None:
			my_cursor.execute(f"UPDATE guild_init SET channel_id='{channel_id}' WHERE server_id='{server_id}';")
			my_db.commit()
			my_cursor.close()
			my_db.close()
			return
		my_cursor.execute("INSERT INTO guild_init (server_id, channel_id) VALUES (%s, %s);", (server_id, channel_id))
		my_db.commit()
		my_cursor.close()
		my_db.close()
	except Exception as e:
		my_cursor.close()
		my_db.close()
		print(e)


def add_user_db(riot_pseudo, user_tag, encrypted_id, discord_user, server_id):
	"""
	Add a user to the DB. The user is added only if the account exists.
	:param riot_pseudo: pseudo of the account to add. Must be a str.
	:param user_tag: tag of the account to add. Must be a str.
	:param discord_user: pseudo of the discord user who added the account. Must be a str.
	:param server_id: id of the discord server. Must be a str. server_id is referenced in guild_init table.
	"""
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		my_cursor.execute(
			"INSERT INTO users_lol ("
			"lol_username, "
			"user_tag, "
			"encrypted_id, "
			"discord_user, "
			"server_id, "
			"in_game, "
			"division_solo, "
			"tier_solo, "
			"league_points_solo, "
			"division_flex, "
			"tier_flex, "
			"league_points_flex"
			") VALUES (%s, %s, %s, %s, %s, 0, 'no tier', 'no division', 0, 'no tier', 'no division', 0);",
			(riot_pseudo, user_tag, encrypted_id, discord_user, server_id))
		my_db.commit()
		my_cursor.close()
		my_db.close()
		return f"The account **_{riot_pseudo}#{user_tag}_** has been added."
	except Exception as e:
		my_cursor.close()
		my_db.close()
		return e


def delete_user_db(riot_pseudo, tag, server_id):
	"""
	Delete a user from the DB using his riot pseudo, tag and channel id.
	:param riot_pseudo: pseudo of the riot account to delete. Must be a str.
	:param tag: tag of the riot account to delete. Must be a str.
	:param server_id: server id from where the slash command is called.
	"""
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		my_cursor.execute(f"DELETE FROM users_lol WHERE lol_username='{riot_pseudo}' AND user_tag='{tag}' AND server_id='{server_id}';")
		rows_affected = my_cursor.rowcount
		my_db.commit()
		my_cursor.close()
		my_db.close()
		if rows_affected == 0:
			return f"No account found for **_{riot_pseudo}#{tag}_** on your server."
		else:
			return f"The account **_{riot_pseudo}#{tag}_** has been removed from your server."
	except Exception as e:
		my_cursor.close()
		my_db.close()
		return e


def update_user_in_game(pseudo, tag, in_game):
	"""
	Update the in_game field of a user.
	:param pseudo: pseudo of the account to update. Must be a str.
	:param in_game: True if the account is in game, False otherwise. Must be a bool.
	"""
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		my_cursor.execute(f"UPDATE users_lol SET in_game='{in_game}' WHERE lol_username='{pseudo}' and user_tag='{tag}';")
		my_db.commit()
		my_cursor.close()
		my_db.close()
	except Exception as e:
		my_cursor.close()
		my_db.close()
		print(e)


def update_league_points(pseudo, tag, league_points, queue):
	"""
	Update the league_points field of a user. Sets a new value for the given queue.
	:param pseudo: pseudo of the account to update. Must be a str.
	:param league_points: new league points value. Must be an int.
	:param queue: queue to update. Must be an int.
	"""
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		if queue == 2:
			my_cursor.execute(f"UPDATE users_lol SET league_points_solo={league_points} WHERE lol_username='{pseudo}' and user_tag='{tag}';")
		elif queue == 0:
			my_cursor.execute(f"UPDATE users_lol SET league_points_flex={league_points} WHERE lol_username='{pseudo}' and user_tag='{tag}';")
		else:
			print("Queue unknown")
			my_cursor.close()
			my_db.close()
			return
		my_db.commit()
		my_cursor.close()
		my_db.close()
		return
	except Exception as e:
		my_cursor.close()
		my_db.close()
		print(e)


def update_division_tier(pseudo, tag, division, tier, queue):
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		if queue == 2:
			my_cursor.execute(
				f"UPDATE users_lol SET division_solo='{division}' WHERE lol_username='{pseudo}' and user_tag='{tag}';")
			my_cursor.execute(
				f"UPDATE users_lol SET tier_solo='{tier}' WHERE lol_username='{pseudo}' and user_tag='{tag}';")
		elif queue == 0:
			my_cursor.execute(
				f"UPDATE users_lol SET division_flex='{division}' WHERE lol_username='{pseudo}' and user_tag='{tag}';")
			my_cursor.execute(
				f"UPDATE users_lol SET tier_flex='{tier}' WHERE lol_username='{pseudo}' and user_tag='{tag}';")
		else:
			print("Queue unknown")
			my_cursor.close()
			my_db.close()
			return
		my_db.commit()
		my_cursor.close()
		my_db.close()
		return
	except Exception as e:
		my_cursor.close()
		my_db.close()
		print(e, file=sys.stderr)


def get_user_by_encrypted_id(encrypted_id, guild_id):
	"""
	Get a user from the DB using his encrypted id.
	:param encrypted_id: encrypted id of the riot account. Must be a str.
	:return row: user from the DB
	"""
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		my_cursor.execute(f"SELECT * FROM users_lol WHERE encrypted_id='{encrypted_id}' AND server_id='{guild_id}';")
		row = my_cursor.fetchone()
		my_db.commit()
		my_cursor.close()
		my_db.close()
	except Exception as e:
		my_cursor.close()
		my_db.close()
		print(e)
		return e
	return row


def get_channel_by_server(server_id):
	"""
	Get the channel to use for a given server.
	:param server_id: id of the discord server. Must be a str. server_id is referenced in guild_init table.
	:return int: id of the channel to use
	"""
	channel_id = -1
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		my_cursor.execute(f"SELECT * FROM guild_init WHERE server_id='{server_id}';")
		row = my_cursor.fetchone()
		channel_id = int(row[1])
		my_db.commit()
		my_cursor.close()
		my_db.close()
	except Exception as e:
		my_cursor.close()
		my_db.close()
		print(e)
		return e
	return channel_id


def get_all_user():
	"""
	Get all users from the DB.
	:return:
	"""
	try:
		my_db = connector_db()
		my_cursor = my_db.cursor()
		my_cursor.execute("USE discord_lol;")
		my_cursor.execute("SELECT * FROM users_lol;")
		rows = my_cursor.fetchall()
		my_cursor.close()
		my_db.close()
		return rows
	except Exception as e:
		print(e)
		return None


def get_all_user_server(server_id):
	"""
	Get all users from the DB.
	:return:
	"""
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		my_cursor.execute(f"SELECT * FROM users_lol WHERE server_id='{server_id}';")
		rows = my_cursor.fetchall()
		my_cursor.close()
		my_db.close()
	except Exception as e:
		my_cursor.close()
		my_db.close()
		print(e)
		return None
	return rows


def get_last_league_points(pseudo, tag, queue):
	"""
	Get the league points of a user. Used to compare the league points before and after a game to get the gain.
	:param pseudo: pseudo of the account to update. Must be a str.
	:param queue: queue to get LP from. Must be an int.
	:return row: league points of the user
	"""
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		if queue == 2:
			my_cursor.execute(f"SELECT league_points_solo FROM users_lol WHERE lol_username='{pseudo}' and user_tag='{tag}';")
		elif queue == 0:
			my_cursor.execute(f"SELECT league_points_flex FROM users_lol WHERE lol_username='{pseudo}' and user_tag='{tag}';")
		else:
			print("Queue unknown")
			my_cursor.close()
			my_db.close()
			return
		row = my_cursor.fetchone()
		my_cursor.close()
		my_db.close()
	except Exception as e:
		my_cursor.close()
		my_db.close()
		print(e)
		return None
	return row


def get_last_tier(pseudo, tag, queue):
	"""
	Get the last tier of a user. Used to compare the league points before and after a game to get the gain.
	:param pseudo: pseudo of the account to update. Must be a str.
	:param queue: queue to get LP from. Must be an int.
	:return row: tier of the user
	"""
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		if queue == 2:
			my_cursor.execute(f"SELECT tier_solo FROM users_lol WHERE lol_username='{pseudo}' and user_tag='{tag}';")
		elif queue == 0:
			my_cursor.execute(f"SELECT tier_flex FROM users_lol WHERE lol_username='{pseudo}' and user_tag='{tag}';")
		else:
			print("Queue unknown")
			my_cursor.close()
			my_db.close()
			return
		row = my_cursor.fetchone()
		my_cursor.close()
		my_db.close()
	except Exception as e:
		my_cursor.close()
		my_db.close()
		print(e)
		return None
	return row


def get_last_division(pseudo, tag, queue):
	"""
	Get the last division of a user. Used to compare the league points before and after a game to get the gain.
	:param pseudo: pseudo of the account to update. Must be a str.
	:param queue: queue to get LP from. Must be an int.
	:return row: division of the user
	"""
	my_db = connector_db()
	my_cursor = my_db.cursor()
	try:
		my_cursor.execute("USE discord_lol;")
		if queue == 2:
			my_cursor.execute(f"SELECT division_solo FROM users_lol WHERE lol_username='{pseudo}' and user_tag='{tag}';")
		elif queue == 0:
			my_cursor.execute(f"SELECT division_flex FROM users_lol WHERE lol_username='{pseudo}' and user_tag='{tag}';")
		else:
			print("Queue unknown")
			my_cursor.close()
			my_db.close()
			return
		row = my_cursor.fetchone()
		my_cursor.close()
		my_db.close()
	except Exception as e:
		my_cursor.close()
		my_db.close()
		print(e)
		return None
	return row
