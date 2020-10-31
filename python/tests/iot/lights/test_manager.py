from mongomock import MongoClient

import pytest


@pytest.fixture()
def discover_bulbs(monkeypatch, bulb):

    def mock_discover_bulbs():
        return [
            {
                'ip': '192.168.0.20',
                'capabilities': {
                    'name': 'Some light'
                }
            }
        ]

    monkeypatch.setattr('iot_app.iot.lights.manager.discover_bulbs', mock_discover_bulbs)


@pytest.fixture()
def db_lights(monkeypatch, discover_bulbs):
    data = {
        'ip': '192.168.0.20',
        'name': 'Some light',
        'is_default': True
    }

    collection = MongoClient()['db']['collection']
    _id = collection.insert_one(data).inserted_id

    def get_lights_from_db():
        return collection.find({'_id': _id})

    monkeypatch.setattr('iot_app.iot.lights.manager.db.get_lights', get_lights_from_db)


def test_manager_singleton(discover_bulbs):
    from iot_app.iot.lights.manager import LightManager

    first_inst = LightManager.instance()
    second_inst = LightManager.instance()

    assert first_inst is second_inst


def test_get_by_name_exists(db_lights):
    from iot_app.iot.lights.manager import LightManager

    lm = LightManager.instance()

    assert lm.get_light_by_name('Some light').ip == '192.168.0.20'


def test_get_by_name_doesnt_exist(db_lights):
    from iot_app.iot.lights.manager import LightManager

    lm = LightManager.instance()

    assert lm.get_light_by_name('No such light') is None

