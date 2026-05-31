import os
import shutil
import config

def get_banner_path(app_id):
    """Returns the path to the banner, caching it if necessary."""
    our_cache_file = os.path.join(config.IMAGE_CACHE_DIR, f"{app_id}.jpg")
    
    # 1. Return if already in local cache
    if os.path.exists(our_cache_file):
        return our_cache_file
    
    # 2. Search Steam folders
    steam_path = find_steam_banner(app_id)
    
    # 3. Cache if found
    if steam_path and os.path.exists(steam_path):
        try:
            shutil.copy(steam_path, our_cache_file)
            return our_cache_file
        except Exception as e:
            print(f"DEBUG: Could not cache image: {e}")
            return steam_path # Return the source if cache fails
            
    return None

def find_steam_banner(app_id):
    cache_base = os.path.expanduser("~/.steam/steam/appcache/librarycache/")
    for root, dirs, files in os.walk(cache_base):
        if str(app_id) in root:
            if "library_header.jpg" in files:
                return os.path.join(root, "library_header.jpg")
            if "header.jpg" in files:
                return os.path.join(root, "header.jpg")
    return None