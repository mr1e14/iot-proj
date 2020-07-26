from iot_app.logger import get_logger
from iot_app.db.lights import save_light, save_new_light, get_lights, get_one_light
from iot_app.config import config

from typing import List, Dict
from yeelight import Bulb, Flow, discover_bulbs, BulbException
from yeelight.transitions import *
from webcolors import hex_to_rgb, rgb_to_hex, normalize_hex

from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime, timedelta

import threading

import time

logging = get_logger(__name__)

_lights_config = config['lights']

class Color:

    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue

    def from_rgb_int(rgb_int: int):
        blue = rgb_int & 255
        green = (rgb_int >> 8) & 255
        red = (rgb_int >> 16) & 255
        return Color(red=red, green=green, blue=blue)

    def from_hex(hex: str):
        try:
            normalized_hex = normalize_hex(hex)
            red, green, blue = hex_to_rgb(normalized_hex)
            return Color(red=red, green=green, blue=blue)
        except ValueError as err:
            logging.error(err)
            raise ValueError('Hex color value supplied is invalid')
        
    @property
    def rgb_dict(self) -> Dict:
        return {
            'red': self.red,
            'green': self.green,
            'blue': self.blue
        }

    @property
    def rgb_tuple(self):
        return (self.red, self.green, self.blue)

    @property
    def hex(self):
        return rgb_to_hex(self.rgb_tuple)


class Light(Bulb):

    db_props = ('name', 'is_default', 'ip')
    bulb_props = ('on', 'brightness', 'color', 'is_flowing')

    def __init__(self, ip, _id, name, is_default, is_connected):
        super().__init__(ip)
        self.__id = _id
        self.__name = name
        self.__is_default = is_default
        self.__is_connected = is_connected
        self.__lock = threading.Lock()


    def refresh_props(self):
        with self.__lock:
            logging.debug(f'Refreshing props of light, IP: {self.ip}')
            props = self.get_properties()
            self.__brightness = int(props['bright'])
            self.__on = props['power'] == 'on'
            rgb_int = int(props['rgb'])
            self.__color = Color.from_rgb_int(rgb_int)
            self.__is_flowing = props['flowing'] == 'flowing'

    def get_prop(self, prop: str) -> str:
        return self.get_properties([prop]).get(prop)

    def dump_props(self) -> Dict:
        props = {
            'id': str(self.id),
            'ip': self.ip,
            'name': self.name,
            'is_default': self.is_default,
            'is_connected': self.is_connected
        }
        if self.is_connected:
            props = {**props,
                'brightness': self.brightness,
                'on': self.on,
                'color': self.color.hex,
                'is_flowing': self.is_flowing
            }
        return props

    def __save(self):
        save_light({'ip': self.ip,
            'name': self.name,
            'is_default': self.is_default},
            _id=self.id
        )

    @property
    def ip(self):
        return self._ip

    @property
    def id(self):
        return self.__id

    @property
    def is_connected(self):
        return self.__is_connected
    
    @property
    def name(self):
        return self.__name
    
    @name.setter
    def name(self, new_name):
        max_light_length = _lights_config['max_light_length']
        if len(new_name) > max_light_length:
            raise ValueError(f'Light name may have a maximum of {max_light_length} characters')
        self.__name = new_name
        self.__save()

    @property
    def is_default(self):
        return self.__is_default
    
    @is_default.setter
    def is_default(self, new_is_default):
        self.__is_default = new_is_default
        self.__save()

    @property
    def brightness(self):
        return self.__brightness

    @brightness.setter
    def brightness(self, new_brightness):
        if not 1 <= new_brightness <= 100:
            raise ValueError('Brightness must be between 1 and 100')
        self.set_brightness(new_brightness)
        self.__brightness = new_brightness

    @property
    def color(self):
        return self.__color

    @color.setter
    def color(self, new_color):
        """ Sets light color
        :param new_color: Color object, hex string or RGB tuple
        Sets to Color object so will try to convert if str or tuple provided
        """
        if not isinstance(new_color, (Color, str, tuple)):
            raise ValueError('Color must be Color object, hex string or RGB tuple')
        color_obj = None
        if isinstance(new_color, Color):
            color_obj = new_color
        elif isinstance(new_color, str):
            color_obj = Color.from_hex(new_color)
        else:
            color_obj = Color(*new_color)
        
        self.set_rgb(**color_obj.rgb_dict)
        self.__color = color_obj
    

    @property
    def on(self):
        return self.__on
    
    @on.setter
    def on(self, new_on: bool):
        if new_on:
            self.turn_on()
        else:
            self.turn_off()
        self.__on = new_on

    @property
    def is_flowing(self):
        return self.__is_flowing

    def __setattr__(self, name, value):
        if hasattr(self, '__lock'):
            with self.__lock:
                try:
                    super(Light, self).__setattr__(name, value)
                except BulbException as err:
                    # bulb no longer online
                    logging.error(err)
                    self.__is_connected = False
                    raise err

        super(Light, self).__setattr__(name, value)


def _create_light(db_data: Dict, is_connected: bool) -> Light:
    logging.info(f'Creating light with IP: {db_data["ip"]}')
    light = Light(**db_data, is_connected=is_connected)

    if is_connected:
        light.refresh_props()
    return light


def _discover_lights() -> List[Light]:
    logging.info('Initializing lights')

    db_lights = get_lights()
    logging.debug(f'Found {db_lights.count()} lights in database')

    ips = []
    for instance in discover_bulbs():
        ips.append(instance['ip'])
        if instance['ip'] not in db_lights.distinct('ip'):
            # save newly discovered light in db
            save_new_light({
                'ip': instance['ip'],
                'name': instance['capabilities']['name'],
                'is_default': False
            })
            # refresh db_lights
            db_lights = get_lights()

    logging.debug(f'Found {len(ips)} lights currently turned on')

    lights = []

    with ThreadPoolExecutor() as executor:
        for db_light in db_lights:
            executor.submit(
                _create_light, db_light, db_light['ip'] in ips
                ).add_done_callback(
                    lambda future: lights.append(future.result())
                )
    return lights

class NotificationLevel:
    #    R   G    B
    OK = 0,  255, 100
    INFO = 0, 150, 255
    WARNING = 255, 150, 0
    ERROR = 255, 0, 50


class LightManager:
    __instance = None

    def __init__(self):
        if LightManager.__instance is None:
            self.__do_lights_discovery()
            LightManager.__instance = self

    def instance():
        if LightManager.__instance is None:
            LightManager()
        return LightManager.__instance

    def get_light_by_name(self, name):
        for light in self.__lights:
            if light.name == name.upper():
                return light
        return None

    @property
    def default_lights(self):
        return [light for light in self.__lights if light.is_default]

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
        flow = Flow(count=3, transitions=pulse(red, green, blue, duration=_lights_config['notify_duration']))

        if len(bulbs) == 0:
            bulbs = [self.default_light]

        for bulb in bulbs:
            bulb.start_flow(flow)

    def stop_flow(self, *bulbs):
        logging.info('Stopping flow')

        if len(bulbs) == 0:
            bulbs = [self.default_light]

        for bulb in bulbs:
            bulb.stop_flow()

    def get_all_lights(self) -> List[Light]:
        return self.__lights

    def __do_lights_discovery(self) -> List[Light]:
        self.__lights = _discover_lights()
        thread = threading.Timer(_lights_config['discovery_interval'], self.__do_lights_discovery)
        thread.daemon = True
        thread.start()
