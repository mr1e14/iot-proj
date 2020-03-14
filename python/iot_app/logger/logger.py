import logging
import logging.handlers
import os

app_dir = os.path.join(os.getcwd(), 'iot_app')
logs_dir = os.path.join(app_dir, 'logs')

def get_logger(module_name: str) -> logging.Logger:
    logger = logging.getLogger(module_name)
    _configure_logger(logger)
    return logger


def _configure_logger(logger: logging.Logger):
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    file_handler = logging.handlers.TimedRotatingFileHandler(os.path.join(logs_dir, 'app.log'), when='D', interval=1, backupCount=7)
    file_handler.setLevel(logging.INFO)
    error_file_handler = logging.handlers.TimedRotatingFileHandler(os.path.join(logs_dir, 'error.log'), when='D', interval=1, backupCount=7)
    error_file_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    ch.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    error_file_handler.setFormatter(formatter)
    
    logger.addHandler(ch)
    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)