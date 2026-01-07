from logging.handlers import TimedRotatingFileHandler
import logging
import os

def get_logger(log_path, base_log_name, name="gnr_logger"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    # Rotating handler: creates new log each day automatically
    file_handler = TimedRotatingFileHandler(
        os.path.join(log_path, base_log_name),
        when="midnight",
        interval=1,
        backupCount=30  # keep last 30 days
    )
    formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
