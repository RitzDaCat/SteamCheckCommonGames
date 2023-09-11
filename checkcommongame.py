import requests
import pandas as pd
from collections import Counter

def get_steam_id(api_key, vanity_url):
    """Fetch Steam ID from vanity URL."""
    try:
        base_url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
        params = {
            "key": api_key,
            "vanityurl": vanity_url
        }
        response = requests.get(base_url, params=params).json()
        
        if response['response']['success'] == 1:
            return response['response']['steamid']
        else:
            return None
    except Exception as e:
        print(f"Error fetching Steam ID for {vanity_url}: {e}")
        return None

def is_profile_public(api_key, steam_id):
    """Check if the Steam profile is public."""
    try:
        base_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            "key": api_key,
            "steamids": steam_id
        }
        response = requests.get(base_url, params=params).json()
        return response['response']['players'][0]['communityvisibilitystate'] == 3
    except Exception as e:
        print(f"Error checking profile visibility for {steam_id}: {e}")
        return False

def get_owned_games(api_key, steam_id):
    """Fetch list of games owned by the given Steam ID."""
    try:
        base_url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
        params = {
            "key": api_key,
            "steamid": steam_id,
            "include_appinfo": 1,
            "format": "json"
        }
        response = requests.get(base_url, params=params).json()
        
        if 'games' in response['response']:
            return [(game['name'], game['playtime_forever'] // 60) for game in response['response']['games']]
        else:
            return []
    except Exception as e:
        print(f"Error fetching owned games for {steam_id}: {e}")
        return []

def find_common_games(api_key, vanity_urls):
    """Find common games among a list of users."""
    game_counter = Counter()
    user_games_dict = {}
    
    for vanity_url in vanity_urls:
        user_games_dict[vanity_url] = "Unable to query"
        steam_id = get_steam_id(api_key, vanity_url)
        if steam_id:
            if is_profile_public(api_key, steam_id):
                games = get_owned_games(api_key, steam_id)
                if games:
                    game_counter.update([game[0] for game in games])
                    user_games_dict[vanity_url] = games
                else:
                    user_games_dict[vanity_url] = "No games found"
            else:
                user_games_dict[vanity_url] = "Profile not public"
    
    common_games = [game for game, count in game_counter.items() if count == len(vanity_urls)]
    return user_games_dict, common_games

def main():
    API_KEY = "API KEY"  # Replace this with your actual API key
    vanity_urls = input("Enter the Steam vanity URLs or usernames of the users, separated by commas: ").split(',')
    vanity_urls = [url.strip() for url in vanity_urls]
    
    user_games_dict, common_games = find_common_games(API_KEY, vanity_urls)
    
    # Create DataFrame
    max_games = max(len(games) if isinstance(games, list) else 1 for games in user_games_dict.values())
    df = pd.DataFrame(index=range(max_games), columns=user_games_dict.keys())
    
    for user, games in user_games_dict.items():
        if isinstance(games, list):
            games_with_playtime = [f"{game[0]} ({game[1]} hrs)" for game in games]
            df[user] = pd.Series(games_with_playtime)
        else:
            df.at[0, user] = games
    
    common_games_with_playtime = [f"{game} (common)" for game in common_games]
    df['Common Games'] = pd.Series(common_games_with_playtime)
    
    # Save to Excel
    df.to_excel("Common_Games.xlsx", index=False)
    print("The list of games and common games has been saved to 'Common_Games.xlsx'.")

if __name__ == "__main__":
    main()
