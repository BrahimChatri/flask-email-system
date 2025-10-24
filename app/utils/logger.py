import logging
import os

os.makedirs("logs", exist_ok=True)

# Formatters
detailed_formatter = logging.Formatter("[%(asctime)s | %(name)s] %(message)s")
simple_formatter = logging.Formatter("-> %(message)s")

# Handlers
file_handler = logging.FileHandler("logs/logs.log")
file_handler.setFormatter(detailed_formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(simple_formatter)

# Function to create a logger
def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if logger already exists
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    
    return logger

# Pre-configured loggers
info_logger = get_logger("INFO", logging.INFO)
error_logger = get_logger("ERROR", logging.ERROR)
