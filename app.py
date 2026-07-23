"""YouTube Downloader Desktop Application Entry Point."""

import sys
from pathlib import Path

# Add project root directory to python path
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from downloader.downloader import YoutubeDownloader
from gui.main_window import MainWindow
from utils.config import ConfigManager


def main() -> None:
    """Initialize dependencies and launch desktop GUI application."""
    config_manager = ConfigManager(base_dir=project_root)
    downloader = YoutubeDownloader(config_manager=config_manager)

    app = MainWindow(config_manager=config_manager, downloader=downloader)
    app.mainloop()


if __name__ == "__main__":
    main()
