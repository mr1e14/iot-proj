from pymongo import MongoClient
from iot_app.config import config

_db_config = config['db']

_conn = MongoClient(host=_db_config['host'], port=_db_config['port'])

db = _conn[_db_config['name']]
