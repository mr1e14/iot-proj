from unittest.mock import MagicMock

import pytest
import mongomock


@pytest.fixture(autouse=True)
def patch_logging(monkeypatch):
    mock_logger = MagicMock()

    def get_logger(module_name):
        mock_logger.module_name = module_name
        return mock_logger
    monkeypatch.setattr('iot_app.logger.get_logger', get_logger)


@pytest.fixture(autouse=True)
def patch_mongo(monkeypatch):
    conn = mongomock.MongoClient()
    db = conn['some_db']

    def get_collection(name):
        return db[name]
    monkeypatch.setattr('iot_app.db.manager.DatabaseManager.get_collection', get_collection)
