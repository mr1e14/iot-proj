import pytest
import mongomock


@pytest.fixture(autouse=True)
def patch_mongo(monkeypatch):
    conn = mongomock.MongoClient()
    db = conn['some_db']

    def get_collection(name):
        return db[name]
    monkeypatch.setattr('iot_app.db.manager.DatabaseManager.get_collection', get_collection)