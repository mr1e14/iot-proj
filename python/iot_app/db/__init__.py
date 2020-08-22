from iot_app.config import secrets
from iot_app.logger import get_logger

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from functools import wraps

logging = get_logger(__name__)

_db_config = secrets['db']
_conn = MongoClient(host=_db_config['host'], port=_db_config['port'])
db = _conn[_db_config['name']]


def handle_mongo_error(func):
    @wraps(func)
    def error_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionFailure as err:
            logging.error(err)
            raise err
    return error_wrapper
