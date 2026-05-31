import tkinter as tk
import sv_ttk
from ui.main_window import SteamLaunchBuilder

if __name__ == "__main__":
    app = SteamLaunchBuilder()
    sv_ttk.set_theme("dark")
    app.mainloop()