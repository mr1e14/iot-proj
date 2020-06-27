from iot_app.config import config

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from functools import wraps

_db_config = config['db']

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