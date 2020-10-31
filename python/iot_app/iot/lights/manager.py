from __future__ import annotations

from iot_app.logger import get_logger
from iot_app.config import config
from iot_app.iot.lights.light import Light

from yeelight import discover_bulbs
from concurrent.futures.thread import ThreadPoolExecutor
from bson.objectid import ObjectId
from typing import List, Dict

import iot_app.db.lights as db

import threading

logging = get_logger(__name__)
_lights_config = config['lights']


class NotificationLevel:
    #    R   G    B
    OK = 0, 255, 100
    INFO = 0, 150, 255
    WARNING = 255, 150, 0
    ERROR = 255, 0, 50


class LightManager:
    __instance = None

    def __init__(self):
        if LightManager.__instance is None:
            self.__lights = []
            self.__do_lights_discovery()
            LightManager.__instance = self

    def get_light_by_name(self, name):
        for light in self.__lights:
            if light.name.upper() == name.upper():
                return light
        return None

    def get_light_by_id(self, _id: str):
        for light in self.__lights:
            if light.id == ObjectId(_id):
                return light
        return None

    @property
    def default_lights(self):
        return [light for light in self.__lights if light.is_default]

    def get_all_lights(self) -> List[Light]:
        return self.__lights

    def __do_lights_discovery(self):
        """
        Scans the network for smart bulbs and records them in the database.
        Also, creates Light objects of known lights (both connected and disconnected)
        """
        connected_bulbs = discover_bulbs()
        LightManager.__save_new_lights(connected_bulbs)

        db_lights = db.get_lights()
        logging.debug(f'Found {db_lights.count()} lights in database')

        with ThreadPoolExecutor() as executor:
            for db_light in db_lights:
                if self.__get_light_by_ip(db_light['ip']) is None:
                    is_connected = db_light['ip'] in [bulb['ip'] for bulb in connected_bulbs]
                    executor.submit(
                        Light, **db_light, is_connected=is_connected
                    ).add_done_callback(
                        lambda future: self.__lights.append(future.result())
                    )
        thread = threading.Timer(_lights_config['discovery_interval'], self.__do_lights_discovery)
        thread.daemon = True
        thread.start()

    def __get_light_by_ip(self, ip):
        for light in self.__lights:
            if light.ip == ip:
                return light
        return None

    @staticmethod
    def instance() -> LightManager:
        if LightManager.__instance is None:
            LightManager()
        return LightManager.__instance

    @staticmethod
    def __save_new_lights(bulb_info: List[Dict]):
        """
        Saves bulbs that are not yet in the database
        :param bulb_info: list of dictionaries, each representing information about an individual bulb, currently
        connected on the network
        """
        db_lights = db.get_lights()
        for bulb in bulb_info:
            if bulb['ip'] not in db_lights.distinct('ip'):
                db.save_new_light({
                    'ip': bulb['ip'],
                    'name': bulb['capabilities']['name'],
                    'is_default': False
                })
