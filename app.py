import sys
import traceback
from pathlib import Path

project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
except Exception:
    pass

from downloader.downloader import YoutubeDownloader
from gui.main_window import MainWindow
from utils.config import ConfigManager


def main() -> None:
    try:
        config_manager = ConfigManager(base_dir=project_root)
        downloader = YoutubeDownloader(config_manager=config_manager)

        app = MainWindow(config_manager=config_manager, downloader=downloader)
        app.mainloop()
    except Exception as e:
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
