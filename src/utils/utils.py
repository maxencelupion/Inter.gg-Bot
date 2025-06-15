def format_riot_account_markdown(riot_username: str, user_tag: str):
    """
    Format Riot account username and tag into a standardized markdown format.
    :param riot_username: Riot account username
    :param user_tag: Riot account tag
    :return: Formatted Riot account string to be displayed in Discord
    """
    return f"**_{riot_username}#{user_tag}_**"

def format_riot_account_error(riot_username: str, user_tag: str):
    """
    Format Riot account username and tag into a standardized discord format.
    :param riot_username: Riot account username
    :param user_tag: Riot account tag
    :return: Formatted Riot account string to be displayed in error output
    """
    return f"{riot_username}#{user_tag}"