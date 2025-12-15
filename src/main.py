import os
import sys

from dotenv import load_dotenv
from loguru import logger

from src.gui import create_main_interface

load_dotenv()

# setup level of logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "ERROR").upper()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL)


def gui():
    """Launch the GUI interface."""
    iface = create_main_interface()
    iface.launch(inbrowser=True)


if __name__ == "__main__":
    gui()
