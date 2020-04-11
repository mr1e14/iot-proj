from pymongo import MongoClient
from iot_app.config import config

_db_config = config['db']

_conn = MongoClient(host=_db_config['host'], port=_db_config['port'])

db = _conn[_db_config['name']]

def handle_mongo_error(func):
    def error_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionFailure as err:
            logging.error(err)
            raise err
    return error_wrapper