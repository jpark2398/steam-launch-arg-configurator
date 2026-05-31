import os
import sys
import json

# Standardize path: ~/.config/steam-launch-arg-configurator
USER_CONFIG_DIR = os.path.expanduser("~/.config/steam-launch-arg-configurator")
os.makedirs(USER_CONFIG_DIR, exist_ok=True)

# Define file and directory paths within that config folder
OPTIONS_FILE = os.path.join(USER_CONFIG_DIR, "launch_options.json")
IMAGE_CACHE_DIR = os.path.join(USER_CONFIG_DIR, "img_cache")
os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)

# Default Options Dictionary
DEFAULT_OPTIONS = {
    "Rendering API": {
        "desc": "Forces specific rendering API",
        "type": "arg",
        "subtype": "select",
        "options": {
            "Vulkan": "-vulkan",
            "DirectX 11": "-dx11",
            "DirectX 12": "-dx12",
            "OpenGL": "-gl"
        }
    },
    "OBS Capture": {
        "desc": "OBS Vulkan Capture Hook",
        "type": "env",
        "subtype": "toggle",
        "options": {
            "Enable": "OBS_VKCAPTURE=1",
            "Disable": "OBS_VKCAPTURE=0"
        }
    },
    "DLSS Upgrade": {
        "desc": "Upgrade DLSS to latest version (DLSS 4.5)",
        "type": "env",
        "subtype": "toggle",
        "options": {
            "Enable": "PROTON_DLSS_UPGRADE=1",
            "Disable": "PROTON_DLSS_UPGRADE=0"
        }
    },
    "DLSS Preset Selector": {
        "desc": "Forces the use of a specific DLSS render preset",
        "type": "env",
        "subtype": "select",
        "options": {
            "Latest": "DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE_RENDER_PRESET_SELECTION=RENDER_PRESET_LATEST",
            "M (DLSS 4.5)": "DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE_RENDER_PRESET_SELECTION=RENDER_PRESET_M",
            "Default (Auto Switcher)": "DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE_RENDER_PRESET_SELECTION=DEFAULT"
        }
    },
    "DLSS Indicator": {
        "desc": "Displays DLSS info in-game",
        "type": "env",
        "subtype": "toggle",
        "options": {
            "Enable": "PROTON_DLSS_INDICATOR=1",
            "Disable": "PROTON_DLSS_INDICATOR=0"
        }
    },
    "Wayland Support": {
        "desc": "Forces display natively with Wayland",
        "type": "env",
        "subtype": "toggle",
        "options": {
            "Enable": "PROTON_ENABLE_WAYLAND=1",
            "Disable": "PROTON_ENABLE_WAYLAND=0"
        }
    },
    "VKD3D Heap": {
        "desc": "Nvidia VKD3D descriptor heap enable",
        "type": "env",
        "subtype": "toggle",
        "options": {
            "Enable": "PROTON_VKD3D_HEAP=1",
            "Disable": "PROTON_VKD3D_HEAP=0"
        }
    },
    "VKD3D Options": {
        "desc": "Advanced VKD3D options",
        "type": "env",
        "subtype": "choices",
        "options": {
            "Descriptor Heap": "descriptor_heap"
        },
        "prefix": "VKD3D_CONFIG=",
        "separator": ","
    }
}

def load_launch_options():
    if not os.path.exists(OPTIONS_FILE):
        # If user file doesn't exist, create it from the default
        with open(OPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_OPTIONS, f, indent=4)
    
    with open(OPTIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_resource_path(relative_path):
    """ Get the absolute path to a resource """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

LAUNCH_OPTIONS = load_launch_options()