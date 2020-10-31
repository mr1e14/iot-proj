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


@pytest.fixture()
def bulb(monkeypatch):
    from yeelight import BulbException

    class MockBulb:
        def __init__(self):
            self.__ip = ''
            # connected by default
            self.__bulb_properties = {
                'bright': 50,
                'rgb': 16711935,
                'flowing': 0,
                'power': 'on'
            }
            self.__on = True
            self.is_connected = True

        def set_ip(self, ip):
            self.__ip = ip

        def get_properties(self):
            self.__raise_if_disconnected()
            return self.__bulb_properties

        def start_flow(self, *args):
            self.__raise_if_disconnected()

        def stop_flow(self):
            self.__raise_if_disconnected()

        def set_rgb(self, **kwargs):
            self.__raise_if_disconnected()

        def set_brightness(self, *args):
            self.__raise_if_disconnected()

        def turn_on(self):
            self.__raise_if_disconnected()
            self.__on = True

        def turn_off(self):
            self.__raise_if_disconnected()
            self.__on = False

        def __raise_if_disconnected(self):
            if not self.is_connected:
                raise BulbException('Disconnected')

    mock_bulb = MockBulb()

    def get_bulb(ip, *args, **kwargs):
        mock_bulb.set_ip(ip)
        return mock_bulb

    monkeypatch.setattr('iot_app.iot.lights.light.Bulb', get_bulb)
    return mock_bulb
