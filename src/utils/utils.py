def format_riot_account(riot_username: str, user_tag: str):
    """
    Format Riot account username and tag into a standardized format.
    :param riot_username: Riot account username
    :param user_tag: Riot account tag
    :return: Formatted Riot account string to be displayed in Discord
    """
    return f"**_{riot_username}#{user_tag}_**"