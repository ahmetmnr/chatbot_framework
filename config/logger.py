import logging
from pathlib import Path
from datetime import datetime
import sys

# Log klasörünü oluştur
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Log formatı
FORMATTER = logging.Formatter(
    "%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)

# Temel logger konfigürasyonu
def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Konsol çıktısı
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    
    # Dosya çıktısı
    file_handler = logging.FileHandler(
        LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    )
    file_handler.setFormatter(FORMATTER)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger

# Uygulama geneli logger
app_logger = setup_logger("chatbot_app")
