import os
import sys

from dotenv import load_dotenv
from loguru import logger

from src.gui import create_main_interface
from src.config import load_toml_config

load_dotenv()

# load config from toml file
load_toml_config()

# setup level of logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "ERROR").upper()
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL)

custom_css = """
/* --- Chat area --- */
.chatbot-container {
    flex: 1 1 auto;
    height: 65vh !important;       /* ⚖️ good balance */
    max-height: 65vh !important;
    overflow-y: auto !important;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 4px;
}

/* --- Align dropdown and button heights --- */
.small-dropdown {
    height: 60px !important;
    width: 120px !important;
}
"""


def gui():
    """Launch the GUI interface."""
    iface = create_main_interface()
    iface.launch(inbrowser=True, css=custom_css)


if __name__ == "__main__":
    gui()
