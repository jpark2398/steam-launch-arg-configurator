import os
import vdf

def detect_steam_id():
    base_path = os.path.expanduser("~/.steam/steam/userdata/")
    if os.path.exists(base_path):
        folders = [f for f in os.listdir(base_path) if f.isdigit()]
        return folders[0] if folders else None
    return None

def get_vdf_path(steam_id):
    return os.path.expanduser(f"~/.steam/steam/userdata/{steam_id}/config/localconfig.vdf")

def get_library_path():
    return os.path.expanduser("~/.steam/steam/steamapps/libraryfolders.vdf")