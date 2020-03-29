from typing import List, Dict
from yeelight import Bulb, Flow, discover_bulbs, BulbException
from yeelight.transitions import *
from iot_app.logger import get_logger

import os

logging = get_logger(__name__)


class Light(Bulb):

    def __init__(self, ip):
        super().__init__(ip)

    def get_prop(self, prop: str) -> str:
        return self.get_properties([prop]).get(prop)


def _initialize_lights() -> List[Light]:
    logging.info('Initializing lights')
    lights = []

    for instance in discover_bulbs():
        lights.append(Light(instance['ip']))

    logging.debug(f'Found {len(lights)} lights')
    return lights


class Room:
    BEDROOM = 'BEDROOM'
    LOUNGE = 'LOUNGE'


class NotificationLevel:
    #    R   G    B
    OK = 0,  255, 100
    INFO = 0, 150, 255
    WARNING = 255, 150, 0
    ERROR = 255, 0, 50


class LightManager:

    def __init__(self, default_room=Room.LOUNGE):
        self.__lights = _initialize_lights()
        self.__default_room = default_room
        self.__default = self.get_light_by_name(default_room)

    def get_light_by_name(self, name):
        for light in self.__lights:
            if light.get_prop('name').upper() == name.upper():
                return light
        return None

    def start_disco(self, *bulbs):
        logging.info('Starting disco')

        flow = Flow(count=0, transitions=disco())

        if len(bulbs) == 0:
            bulbs = [self.__default]

        for bulb in bulbs:
            bulb.start_flow(flow)

    def notify(self, level=NotificationLevel.INFO, *bulbs):
        logging.info(f'Flashing notification ({level})')

        red, green, blue = level
        flow = Flow(count=3, transitions=pulse(red, green, blue, duration=400))

        if len(bulbs) == 0:
            bulbs = [self.__default]

        for bulb in bulbs:
            bulb.start_flow(flow)

    def stop_flow(self, *bulbs):
        logging.info('Stopping flow')

        if len(bulbs) == 0:
            bulbs = [self.__default]

        for bulb in bulbs:
            bulb.stop_flow()

    def set_default(self, name):
        # TODO default room should be stored in database, not in an instance variable
        light = self.get_light_by_name(name)
        if light is not None:
            self.__default_room = name
            self.__default = self.get_light_by_name(name)
            logging.info(f'Set new default light to {name}')
        else:
            logging.warning(f'Default not set. No such light: {name}')

    def get_all_lights(self):
        return self.__lights

    def get_default_room(self):
        return self.__default_room
