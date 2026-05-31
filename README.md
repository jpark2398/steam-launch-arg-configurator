# Steam Launch Arg Configurator
---


Steam Launch Arg Configurator simplifies your gaming workflow by acting as a powerful launch argument management layer for your Steam library. Instead of manually editing launch options in Steam's properties menu for every game, you can use a centralized interface to streamline the process.

### Key Features
* **Argument Repository**: Create and maintain a persistent list of your most-used launch arguments (e.g., `gamemoderun %command%`, custom VKD3D flags, or resolution overrides).
* **One-Click Application**: Effortlessly apply any argument set from your saved list to any installed game via our intuitive graphical interface.
* **Non-Destructive Management**: Quickly swap between different argument profiles for testing, optimization, or troubleshooting without modifying your Steam library settings files manually.
* **Performance Focused**: Designed to work seamlessly with your existing Steam installation, ensuring your custom configurations are applied exactly when you launch your title.

## Installation

### Automated Install (Recommended)
You can install the latest version automatically by running the following command in your terminal:

```bash
curl -sSL https://raw.githubusercontent.com/jpark2398/steam-launch-arg-configurator/main/install.sh | bash
```

### Manual Installation
1. **Download**: Get the latest `steam-launch-arg-configurator` binary from the [Releases page](https://github.com/YOUR_USERNAME/steam-launch-arg-configurator/releases).
2. **Make Executable**:
    ```bash
    chmod +x steam-launch-arg-configurator
    ```
3. **Move to Path**:
    ```bash
    mkdir -p ~/.local/bin
    mv steam-launch-arg-configurator ~/.local/bin/
    ```

## Usage
Once installed, you can launch the application from your desktop's application menu under **Utilities** > **Steam ARG Util**.

## Development
This project is built with Python, Tkinter, and PyInstaller.

### Build from Source
To build the binary yourself:
1. Install dependencies: `pip install -r requirements.txt pyinstaller`
2. Run the build command:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --add-data "ui:ui" --add-data "utils:utils" --add-data "icon.png:." --collect-all PIL main.py
    ```

## License
MIT License. See the LICENSE file for more details.

---
*Built with ❤️ for the Steam community.*