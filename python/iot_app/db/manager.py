from iot_app.config import secrets
from pymongo import MongoClient


def _connect():
    db_config = secrets['db']
    conn = MongoClient(host=db_config['host'], port=db_config['port'])
    db = conn[db_config['name']]
    db.authenticate(name=db_config['username'], password=db_config['password'])
    return db


class DatabaseManager:
    """
    Enables interaction with mongo database by handling connection and authentication
    Provides access mongo collections
    """
    __db = None

    @staticmethod
    def get_collection(collection_name: str):
        if DatabaseManager.__db is None:
            DatabaseManager.__db = _connect()
        return DatabaseManager.__db[collection_name]

