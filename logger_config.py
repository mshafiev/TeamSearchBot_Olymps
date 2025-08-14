import logging
import os

# Настройка логгера
logger = logging.getLogger("olymps_service")  # Название логгера

# Установка уровня логирования из переменной окружения (по умолчанию INFO)
_level = os.getenv("LOG_LEVEL", "INFO").upper()
try:
    logger.setLevel(getattr(logging, _level))
except AttributeError:
    logger.setLevel(logging.INFO)

# Формат логов
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')

# Избежать дублирования обработчиков при повторных импортах
if not logger.handlers:
    # Обработчик — в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Обработчик — в файл
    file_handler = logging.FileHandler("app_rmq.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

logger.propagate = False
