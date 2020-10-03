from iot_app.logger import get_logger

from pymongo.errors import ConnectionFailure
from functools import wraps

logging = get_logger(__name__)


def handle_mongo_error(func):
    @wraps(func)
    def error_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionFailure as err:
            logging.error(err)
            raise err
    return error_wrapper


from .manager import DatabaseManager
