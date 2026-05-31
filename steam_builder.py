import os
import time
import subprocess
import shutil
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk
import pyperclip
import vdf
import requests
from PIL import Image, ImageTk

OPTIONS_FILE = os.path.expanduser("~/Projects/steam-arg-util/launch_options.json")
IMAGE_CACHE_DIR = os.path.expanduser("~/Projects/steam-arg-util/img_cache")
os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)

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
        try:
            with open(OPTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_OPTIONS, f, indent=4)
        except Exception as e:
            print(f"Could not create JSON file: {e}")
        return DEFAULT_OPTIONS
    try:
        with open(OPTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Warning: launch_options.json is corrupted or invalid. Using default options.")
        return DEFAULT_OPTIONS

LAUNCH_OPTIONS = load_launch_options()

# --- CUSTOM TOOLTIP CLASS ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(400, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert") or (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#2b2b2b", foreground="#e0e0e0", relief="solid", borderwidth=1,
                         font=("Segoe UI", 9))
        label.pack(ipadx=8, ipady=5)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class SteamLaunchBuilder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Steam Launch Option Manager")
        self.geometry("980x750")
        sv_ttk.set_theme("dark")
        
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png") # or .ico
        if os.path.exists(icon_path):
            try:
                # Load the image as a PhotoImage
                icon_img = tk.PhotoImage(file=icon_path)
                # Set it as the window icon
                self.wm_iconphoto(True, icon_img)
            except Exception as e:
                print(f"Could not set window icon: {e}")

        self.steam_id = self.detect_steam_id()
        self.vdf_path = os.path.expanduser(f"~/.steam/steam/userdata/{self.steam_id}/config/localconfig.vdf") if self.steam_id else None
        self.library_path = os.path.expanduser("~/.steam/steam/steamapps/libraryfolders.vdf")
        self.selected_app_id = None
        self.games_data = {}
        self.card_images = {} # Holds memory references to images so Tkinter doesn't garbage collect them

        self.grid_frame = ttk.Frame(self)
        self.editor_frame = ttk.Frame(self)

        if not self.steam_id or not os.path.exists(self.vdf_path):
            self.show_error_screen("Could not automatically locate your Steam userdata folder.")
        else:
            self.show_loading_screen()
            threading.Thread(target=self.load_games, daemon=True).start()

    def open_about_window(self):
        about_win = tk.Toplevel(self)
        about_win.title("About")
        about_win.geometry("300x150")
        
        ttk.Label(about_win, text="Steam Launch Option Manager", font=("Segoe UI", 10, "bold")).pack(pady=10)
        ttk.Label(about_win, text="Icon attribution:").pack()
        
        link = ttk.Label(about_win, text="Icon by Freepik from Flaticon", foreground="#4c9aff", cursor="hand2")
        link.pack(pady=5)
        link.bind("<Button-1>", lambda e: subprocess.Popen(["xdg-open", "https://www.flaticon.com/free-icon/game-controller_141295"]))
        
        ttk.Button(about_win, text="Close", command=about_win.destroy).pack(pady=10)

    def detect_steam_id(self):
        base_path = os.path.expanduser("~/.steam/steam/userdata/")
        if os.path.exists(base_path):
            folders = [f for f in os.listdir(base_path) if f.isdigit()]
            if folders:
                return folders[0]
        return None

    def load_games(self):
        try:
            self.after(0, lambda: self.loading_label.config(text="Scanning local Steam library..."))
            
            with open(self.vdf_path, 'r', encoding='utf-8') as file:
                config_data = vdf.load(file)
            
            root_key = list(config_data.keys())[0]  
            apps_dict = config_data[root_key]['Software']['Valve']['Steam']['apps']

            with open(self.library_path, 'r', encoding='utf-8') as f:
                lib_data = vdf.load(f)
            
            for lib_key, lib_info in lib_data.get('libraryfolders', {}).items():
                lib_path = lib_info.get('path', '')
                installed_apps = lib_info.get('apps', {}).keys()

                for app_id in installed_apps:
                    manifest_path = os.path.join(lib_path, "steamapps", f"appmanifest_{app_id}.acf")
                    game_name = f"Unknown Game (ID: {app_id})"
                    
                    if os.path.exists(manifest_path):
                        with open(manifest_path, 'r', encoding='utf-8') as mf:
                            try:
                                manifest_data = vdf.load(mf)
                                game_name = manifest_data.get('AppState', {}).get('name', game_name)
                            except Exception:
                                pass
                    
                    if any(tool in game_name for tool in ["Proton", "Steamworks", "Steam Linux Runtime"]):
                        continue
                    
                    current_opts = apps_dict.get(str(app_id), {}).get('LaunchOptions', '')

                    self.games_data[str(app_id)] = {
                        "name": game_name,
                        "current_options": current_opts
                    }

            self.after(0, self.build_grid_view)

        except Exception as e:
            error_msg = f"Error loading config: {str(e)}"
            self.after(0, lambda msg=error_msg: self.show_error_screen(msg))

    def show_loading_screen(self):
        self.loading_label = ttk.Label(self, text="Initializing...", font=("Segoe UI", 14))
        self.loading_label.pack(expand=True)

    def show_error_screen(self, message):
        if hasattr(self, 'loading_label'): self.loading_label.pack_forget()
        err = ttk.Label(self, text=message, foreground="red", font=("Segoe UI", 12))
        err.pack(expand=True)

    def save_launch_options(self):
        try:
            with open(OPTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(LAUNCH_OPTIONS, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save to JSON:\n{str(e)}")

    # --- IMAGE FETCHING LOGIC ---
    def apply_card_image(self, app_id, img_label):
        # 1. Look for Steam's new hashed library cache
        # We start searching from the librarycache folder
        cache_base = os.path.expanduser("~/.steam/steam/appcache/librarycache/")
        our_cache = os.path.join(IMAGE_CACHE_DIR, f"{app_id}.jpg")
        
        img_path_to_use = None
        
        # Search recursively for a file starting with the app_id
        if os.path.exists(cache_base):
            for root, dirs, files in os.walk(cache_base):
                for file in files:
                    # Look for the header image belonging to this app_id
                    if file == "library_header.jpg" and str(app_id) in root:
                        img_path_to_use = os.path.join(root, file)
                        break
                if img_path_to_use: break

        # 2. Fallback to our own cache
        if not img_path_to_use and os.path.exists(our_cache):
            img_path_to_use = our_cache
            
        # 3. Final Web Fallback
        if not img_path_to_use:
            try:
                url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    with open(our_cache, 'wb') as f:
                        f.write(resp.content)
                    img_path_to_use = our_cache
            except:
                pass

        # Final display logic
        if img_path_to_use:
            try:
                img = Image.open(img_path_to_use)
                img = img.resize((184, 86), Image.Resampling.LANCZOS)
                self.after(0, self.set_image_to_label, app_id, img, img_label)
            except:
                self.after(0, lambda: img_label.config(text="[ No Banner ]"))
        else:
            self.after(0, lambda: img_label.config(text="[ No Banner ]"))

    def set_image_to_label(self, app_id, pil_img, img_label):
        photo = ImageTk.PhotoImage(pil_img)
        self.card_images[app_id] = photo 
        img_label.config(image=photo, text="") # Swap the text out for the image

    def build_grid_view(self):
        if hasattr(self, 'loading_label'): self.loading_label.pack_forget()
        self.editor_frame.pack_forget()
        
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        self.card_images.clear() # Clear old memory references
        self.grid_frame.pack(fill="both", expand=True, padx=20, pady=20)

        header_frame = ttk.Frame(self.grid_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        header = ttk.Label(header_frame, text="Installed Games", font=("Segoe UI", 16, "bold"))
        header.pack(side="left")

        manage_btn = ttk.Button(header_frame, text="⚙️ Manage Config", command=self.open_manage_window)
        manage_btn.pack(side="right")

        about_btn = ttk.Button(header_frame, text="ℹ️ About", command=self.open_about_window)
        about_btn.pack(side="right", padx=(0, 10))
    

        canvas = tk.Canvas(self.grid_frame, bg=self.cget('bg'), highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.grid_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units")) # Support for Linux scroll
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))  # Support for Linux scroll
        
        self.grid_frame.rowconfigure(1, weight=1)
        self.grid_frame.columnconfigure(0, weight=1)

        row, col = 0, 0
        for app_id, data in sorted(self.games_data.items(), key=lambda x: x[1]['name']):
            card = ttk.Frame(scrollable_frame, padding=10, style="Card.TFrame")
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Image Container
            img_lbl = ttk.Label(card, text="[ Loading Banner ]", foreground="gray", font=("Segoe UI", 8))
            img_lbl.pack(pady=(0, 5))
            
            # Start a background worker to fetch the image without freezing the UI
            threading.Thread(target=self.apply_card_image, args=(app_id, img_lbl), daemon=True).start()
            
            lbl = ttk.Label(card, text=data['name'], font=("Segoe UI", 10, "bold"), wraplength=180, justify="center")
            lbl.pack(pady=(5, 10))
            
            btn = ttk.Button(card, text="Manage", command=lambda aid=app_id: self.open_editor_view(aid))
            btn.pack(side="bottom")

            col += 1
            if col > 3: # 4 Columns Wide
                col = 0
                row += 1

    def generate_tooltip_text(self, key, info):
        if info.get("subtype") == "toggle":
            opts = "\n".join([f"  • {k}: {v}" for k, v in info.get("options", {}).items()])
            return f"Raw Arguments:\n{opts}"
        return f"Raw Argument:\n{key}"

    def open_editor_view(self, app_id):
        from tkinter import filedialog # Ensure we can open file dialogs

        self.selected_app_id = app_id
        self.grid_frame.pack_forget()
        
        for widget in self.editor_frame.winfo_children():
            widget.destroy()

        self.editor_frame.pack(fill="both", expand=True, padx=20, pady=20)
        game_info = self.games_data[app_id]

        top_bar = ttk.Frame(self.editor_frame)
        top_bar.pack(fill="x", pady=(0, 20))
        
        back_btn = ttk.Button(top_bar, text="← Back to Games", command=self.build_grid_view)
        back_btn.pack(side="left")
        
        title = ttk.Label(top_bar, text=game_info['name'], font=("Segoe UI", 16, "bold"))
        title.pack(side="left", padx=20)

        # Logic to check if we have a custom override
        custom_override_path = os.path.join(IMAGE_CACHE_DIR, f"{app_id}.jpg")
        has_custom = os.path.exists(custom_override_path)
        
        # New Upload Banner Button with logic
        def upload_banner():
            win = tk.Toplevel(self)
            win.title("Upload/Change Banner")
            win.geometry("400x150")
            
            ttk.Label(win, text="Paste path to image file (.jpg/.png):").pack(pady=10)
            path_entry = ttk.Entry(win, width=50)
            path_entry.pack(pady=5, padx=10)
            
            def process_path():
                file_path = path_entry.get().strip().replace("'", "").replace('"', "")
                if os.path.exists(file_path):
                    try:
                        img = Image.open(file_path)
                        img.convert("RGB").save(custom_override_path, "JPEG")
                        messagebox.showinfo("Success", "Banner updated!", parent=win)
                        win.destroy()
                        # Refresh editor to show the update
                        self.open_editor_view(app_id)
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to save image: {e}", parent=win)
                else:
                    messagebox.showerror("Error", "File does not exist.", parent=win)
            
            ttk.Button(win, text="Apply Banner", command=process_path).pack(pady=10)

        # Dynamic button text
        btn_text = "🖼 Change Banner" if has_custom else "🖼 Add Custom Banner"
        upload_btn = ttk.Button(top_bar, text=btn_text, command=upload_banner)
        upload_btn.pack(side="right")

        self.check_vars = {}   
        self.combo_vars = {}   
        self.radio_vars = {}   
        self.choice_vars = {}  
        
        current_opts = game_info['current_options']
        custom_string = current_opts

        checkbox_container = ttk.Frame(self.editor_frame)
        checkbox_container.pack(fill="both", expand=True)

        for key, info in LAUNCH_OPTIONS.items():
            subtype = info.get("subtype", "check")
            
            row_frame = ttk.Frame(checkbox_container)
            row_frame.pack(fill="x", pady=4)
            
            if subtype in ["toggle", "select"]:
                var = tk.BooleanVar()
                self.check_vars[key] = var
                chk = ttk.Checkbutton(row_frame, text=key, variable=var, command=self.update_preview)
                chk.pack(side="left")
                
                if subtype == "toggle":
                    ToolTip(chk, self.generate_tooltip_text(key, info))
                    
                    combo_var = tk.StringVar(value=list(info["options"].keys())[0])
                    self.combo_vars[key] = combo_var
                    
                    for opt_label, opt_val in info["options"].items():
                        if opt_val in current_opts:
                            var.set(True)
                            combo_var.set(opt_label)
                            custom_string = custom_string.replace(opt_val, "")
                            break
                            
                    combo = ttk.Combobox(row_frame, textvariable=combo_var, values=list(info["options"].keys()), state="readonly", width=12)
                    combo.pack(side="left", padx=(10, 0))
                    combo.bind("<<ComboboxSelected>>", lambda e, k=key: self.on_interact(k))
                    
                elif subtype == "select":
                    radio_var = tk.StringVar(value=list(info["options"].keys())[0])
                    self.radio_vars[key] = radio_var
                    
                    for opt_label, opt_val in info["options"].items():
                        if opt_val in current_opts:
                            var.set(True)
                            radio_var.set(opt_label)
                            custom_string = custom_string.replace(opt_val, "")
                            break
                            
                    radio_frame = ttk.Frame(row_frame)
                    radio_frame.pack(side="left", padx=(10, 0))
                    for opt_label, opt_val in info["options"].items():
                        rb = ttk.Radiobutton(radio_frame, text=opt_label, variable=radio_var, value=opt_label, command=lambda k=key: self.on_interact(k))
                        rb.pack(side="left", padx=(0, 5))
                        ToolTip(rb, f"Raw Argument:\n{opt_val}")
                        
                ttk.Label(row_frame, text=f"- {info['desc']}", foreground="gray").pack(side="left", padx=(10, 0))
                
            elif subtype == "choices":
                title_lbl = ttk.Label(row_frame, text=key, font=("Segoe UI", 10, "bold"))
                title_lbl.pack(side="left")
                ttk.Label(row_frame, text=f"- {info['desc']}", foreground="gray").pack(side="left", padx=(10, 0))
                
                choice_frame = ttk.Frame(checkbox_container)
                choice_frame.pack(fill="x", pady=(0, 8), padx=(20, 0)) 
                
                self.choice_vars[key] = {}
                prefix = info.get("prefix", "")
                sep = info.get("separator", ",")
                
                if prefix and prefix in current_opts:
                    custom_string = custom_string.replace(prefix, "")
                    
                for opt_label, opt_val in info["options"].items():
                    c_var = tk.BooleanVar()
                    self.choice_vars[key][opt_label] = c_var
                    
                    if opt_val in current_opts:
                        c_var.set(True)
                        custom_string = custom_string.replace(opt_val, "")
                        
                    c_chk = ttk.Checkbutton(choice_frame, text=opt_label, variable=c_var, command=self.update_preview)
                    c_chk.pack(side="left", padx=(0, 15))
                    ToolTip(c_chk, f"Raw Argument:\n{prefix}{opt_val}")
                    
                custom_string = custom_string.replace(sep, " ")
                
            else: 
                var = tk.BooleanVar()
                self.check_vars[key] = var
                if key in current_opts:
                    var.set(True)
                    custom_string = custom_string.replace(key, "")
                    
                chk = ttk.Checkbutton(row_frame, text=key, variable=var, command=self.update_preview)
                chk.pack(side="left")
                ToolTip(chk, self.generate_tooltip_text(key, info))
                
                ttk.Label(row_frame, text=f"- {info.get('desc', '')}", foreground="gray").pack(side="left", padx=(10, 0))

        if "%command%" in custom_string:
            parts = custom_string.split("%command%")
            self.custom_prefixes = " ".join(parts[0].split())
            self.custom_suffixes = " ".join(parts[1].split())
        else:
            leftovers = custom_string.split()
            prefs, suffs = [], []
            hit_suffix_flag = False
            
            for word in leftovers:
                if word.startswith("-") or word.startswith("+"):
                    hit_suffix_flag = True
                if hit_suffix_flag:
                    suffs.append(word)
                else:
                    prefs.append(word)
                    
            self.custom_prefixes = " ".join(prefs)
            self.custom_suffixes = " ".join(suffs)

        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(self.editor_frame, textvariable=self.output_var, state="readonly", font=("Consolas", 10))
        self.output_entry.pack(fill="x", pady=20)

        actions_frame = ttk.Frame(self.editor_frame)
        actions_frame.pack(fill="x")

        apply_btn = ttk.Button(actions_frame, text="Apply & Relaunch Steam", style="Accent.TButton", command=self.apply_to_steam)
        apply_btn.pack(side="left", padx=(0, 10))
        copy_btn = ttk.Button(actions_frame, text="Copy Text Only", command=self.copy_to_clipboard)
        copy_btn.pack(side="left")

        self.status_label = ttk.Label(actions_frame, text="")
        self.status_label.pack(side="right")
        self.update_preview()

    def on_interact(self, key):
        self.check_vars[key].set(True)
        self.update_preview()

    def update_preview(self):
        envs = []
        args = []
        
        for key, info in LAUNCH_OPTIONS.items():
            subtype = info.get("subtype", "check")
            
            if subtype in ["toggle", "select", "check"]:
                if key in self.check_vars and self.check_vars[key].get():
                    if subtype == "toggle":
                        selected_label = self.combo_vars[key].get()
                        cmd_string = info["options"].get(selected_label, "")
                    elif subtype == "select":
                        selected_label = self.radio_vars[key].get()
                        cmd_string = info["options"].get(selected_label, "")
                    else:
                        cmd_string = key
                        
                    if info["type"] == "env":
                        envs.append(cmd_string)
                    else:
                        args.append(cmd_string)
                        
            elif subtype == "choices":
                selected_vals = []
                for opt_label, c_var in self.choice_vars[key].items():
                    if c_var.get():
                        selected_vals.append(info["options"][opt_label])
                
                if selected_vals:
                    prefix = info.get("prefix", "")
                    sep = info.get("separator", ",")
                    cmd_string = f"{prefix}{sep.join(selected_vals)}"
                    
                    if info["type"] == "env":
                        envs.append(cmd_string)
                    else:
                        args.append(cmd_string)
                        
        parts = []
        if envs: parts.append(" ".join(envs))
        if hasattr(self, 'custom_prefixes') and self.custom_prefixes: parts.append(self.custom_prefixes)
        if envs or (hasattr(self, 'custom_prefixes') and self.custom_prefixes): parts.append("%command%")
        if args: parts.append(" ".join(args))
        if hasattr(self, 'custom_suffixes') and self.custom_suffixes: parts.append(self.custom_suffixes)
            
        self.output_var.set(" ".join(parts))

    def copy_to_clipboard(self):
        text = self.output_var.get()
        if text:
            pyperclip.copy(text)
            self.status_label.config(text="Copied to clipboard!", foreground="#4caf50")

    def apply_to_steam(self):
        launch_string = self.output_var.get()
        self.status_label.config(text="Shutting down Steam...", foreground="orange")
        self.update()

        subprocess.run(["steam", "-shutdown"])
        time.sleep(5) 
        
        try:
            shutil.copy(self.vdf_path, self.vdf_path + ".backup")
            with open(self.vdf_path, 'r', encoding='utf-8') as file:
                config_data = vdf.load(file)
            
            root_key = list(config_data.keys())[0]    
            apps = config_data[root_key]['Software']['Valve']['Steam']['apps']
            if self.selected_app_id not in apps:
                apps[self.selected_app_id] = {}
                
            apps[self.selected_app_id]['LaunchOptions'] = launch_string
            
            with open(self.vdf_path, 'w', encoding='utf-8') as file:
                vdf.dump(config_data, file)
                
            self.games_data[self.selected_app_id]['current_options'] = launch_string
            self.status_label.config(text="Relaunching Steam...", foreground="orange")
            self.update()

            subprocess.Popen(["steam"], start_new_session=True)
            self.status_label.config(text="Success! Configuration saved.", foreground="#4caf50")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred writing configuration:\n{str(e)}")
            self.status_label.config(text="Save failed.", foreground="red")

    def open_manage_window(self):
        manage_win = tk.Toplevel(self)
        manage_win.title("Manage Launch Options")
        manage_win.geometry("550x550")
        manage_win.transient(self)
        manage_win.grab_set()

        notebook = ttk.Notebook(manage_win)
        notebook.pack(fill="both", expand=True, padx=15, pady=15)

        add_frame = ttk.Frame(notebook, padding=20)
        notebook.add(add_frame, text="Add New Option")

        ttk.Label(add_frame, text="Command or Group Name:").pack(anchor="w")
        name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=name_var).pack(fill="x", pady=(0, 10))

        ttk.Label(add_frame, text="Description:").pack(anchor="w")
        desc_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=desc_var).pack(fill="x", pady=(0, 10))

        type_frame = ttk.Frame(add_frame)
        type_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(type_frame, text="Argument Type:").grid(row=0, column=0, sticky="w")
        type_var = tk.StringVar(value="arg")
        ttk.Radiobutton(type_frame, text="Game Argument (-novid)", variable=type_var, value="arg").grid(row=0, column=1, padx=5)
        ttk.Radiobutton(type_frame, text="Environment Var (GAMEMODE=1)", variable=type_var, value="env").grid(row=0, column=2, padx=5)

        ttk.Label(add_frame, text="UI Subtype:").pack(anchor="w")
        subtype_var = tk.StringVar(value="check")
        subtype_combo = ttk.Combobox(add_frame, textvariable=subtype_var, values=["check", "toggle", "select", "choices"], state="readonly")
        subtype_combo.pack(fill="x", pady=(0, 10))

        group_frame = ttk.Frame(add_frame)
        ttk.Label(group_frame, text="Options (Format -> Label:Command, comma separated):", foreground="gray").pack(anchor="w")
        options_var = tk.StringVar()
        ttk.Entry(group_frame, textvariable=options_var).pack(fill="x")

        choices_frame = ttk.Frame(add_frame)
        ttk.Label(choices_frame, text="Prefix (e.g. VKD3D_CONFIG=):").grid(row=0, column=0, sticky="w")
        prefix_var = tk.StringVar()
        ttk.Entry(choices_frame, textvariable=prefix_var, width=18).grid(row=0, column=1, padx=5)
        ttk.Label(choices_frame, text="Separator:").grid(row=0, column=2, sticky="w")
        sep_var = tk.StringVar(value=",")
        ttk.Entry(choices_frame, textvariable=sep_var, width=5).grid(row=0, column=3, padx=5)

        def toggle_frames(*args):
            st = subtype_var.get()
            if st in ["toggle", "select", "choices"]:
                group_frame.pack(fill="x", pady=(0, 10))
            else:
                group_frame.pack_forget()
                
            if st == "choices":
                choices_frame.pack(fill="x", pady=(0, 10))
            else:
                choices_frame.pack_forget()
                
        subtype_var.trace_add("write", toggle_frames)
        toggle_frames()

        def save_new_option():
            name = name_var.get().strip()
            desc = desc_var.get().strip()
            st = subtype_var.get()
            
            if not name or not desc:
                messagebox.showerror("Missing Data", "Name and Description are required.", parent=manage_win)
                return

            new_data = {
                "desc": desc,
                "type": type_var.get(),
                "subtype": st
            }
            
            if st in ["toggle", "select", "choices"]:
                opts_dict = {}
                for r in options_var.get().split(","):
                    if ":" in r:
                        lbl, val = r.split(":", 1)
                        opts_dict[lbl.strip()] = val.strip()
                if not opts_dict:
                    messagebox.showerror("Format Error", "Provide at least one option using the Label:Command format.", parent=manage_win)
                    return
                new_data["options"] = opts_dict
                
                if st == "choices":
                    new_data["prefix"] = prefix_var.get().strip()
                    new_data["separator"] = sep_var.get() or ","

            LAUNCH_OPTIONS[name] = new_data
            self.save_launch_options()
            messagebox.showinfo("Success", f"'{name}' added successfully!", parent=manage_win)
            manage_win.destroy()

        ttk.Button(add_frame, text="Save to Config", style="Accent.TButton", command=save_new_option).pack(pady=20)

        remove_frame = ttk.Frame(notebook, padding=20)
        notebook.add(remove_frame, text="Remove Option")

        ttk.Label(remove_frame, text="Select option to delete:").pack(anchor="w")
        remove_combo_var = tk.StringVar()
        remove_combo = ttk.Combobox(remove_frame, textvariable=remove_combo_var, values=list(LAUNCH_OPTIONS.keys()), state="readonly")
        remove_combo.pack(fill="x", pady=(0, 20))

        def remove_option():
            target = remove_combo_var.get()
            if not target: return
            
            if messagebox.askyesno("Confirm", f"Are you sure you want to permanently remove '{target}' from your configuration?", parent=manage_win):
                del LAUNCH_OPTIONS[target]
                self.save_launch_options()
                messagebox.showinfo("Success", f"'{target}' removed successfully!", parent=manage_win)
                manage_win.destroy()

        ttk.Button(remove_frame, text="Delete Selected", command=remove_option).pack()

if __name__ == "__main__":
    app = SteamLaunchBuilder()
    app.mainloop()