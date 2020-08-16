from __future__ import annotations

from iot_app.logger import get_logger
from iot_app.config import config

from yeelight import Bulb, Flow, discover_bulbs, BulbException
from yeelight.transitions import *
from webcolors import hex_to_rgb, rgb_to_hex, normalize_hex
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List, Dict

import iot_app.db.lights as db
import threading

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

class LightEffect:

    def __init__(self):
        pass

    def get_flow(self) -> Flow:
        raise NotImplementedError

class DiscoEffect(LightEffect):

    def __init__(self, count=0):
        super().__init__()
        self.__count = count

    def get_flow(self):
        return Flow(count=self.__count, transitions=disco())

class StrobeEffect(LightEffect):

    def __init__(self, count=0):
        super().__init__()
        self.__count = count

    def get_flow(self):
        return Flow(count=self.__count, transitions=strobe())

class LSDEffect(LightEffect):

    def __init__(self, duration=1000, count=0):
        super().__init__()
        self.__duration = duration
        self.__count = count

    def get_flow(self):
        return Flow(count=self.__count, transitions=lsd(duration=self.__duration))

class PoliceEffect(LightEffect):

    def __init__(self, count=0, duration=300):
        super().__init__()
        self.__count = count
        self.__duration = duration

    def get_flow(self):
        return Flow(count=self.__count, transitions=police(duration=self.__duration))

class RandomLoopEffect(LightEffect):

    def __init__(self, count=0, duration=500):
        super().__init__()
        self.__count = count
        self.__duration = duration

    def get_flow(self):
        return Flow(count=self.__count, transitions=randomloop(duration=self.__duration))



class Light():

    db_props = ('name', 'is_default', 'ip')
    bulb_props = ('on', 'brightness', 'color', 'is_flowing')
    effects_map = {
        'disco': DiscoEffect,
        'lsd': LSDEffect,
        'police': PoliceEffect,
        'strobe': StrobeEffect,
        'random': RandomLoopEffect
        }

    def __init__(self, ip, _id, name, is_default, is_connected):
        self.__bulb = Bulb(ip, auto_on=True)
        self.__id = _id
        self.__name = name
        self.__is_default = is_default
        self.__is_connected = is_connected
        self.__effect = None
        self.__effect_props = {}
        self.__lock = threading.RLock()


    def refresh_props(self):
        """
        Makes a direct call on the smart bulb to update properties visible via APIs
        """
        with self.__lock:
            logging.debug(f'Refreshing props of light, IP: {self.ip}')
            try:
                props = self.__bulb.get_properties()
                self.__is_connected = True
                self.__brightness = int(props['bright'])
                self.__on = props['power'] == 'on'
                rgb_int = int(props['rgb'])
                self.__color = Color.from_rgb_int(rgb_int)
                self.__is_flowing = props['flowing'] == '1'
            except BulbException as err:
                self.__implied_disconnected()

    def get_prop(self, prop: str) -> str:
        return self.__bulb.get_properties([prop]).get(prop)

    def dump_props(self) -> Dict:
        """
        Create a dictionary of light props. Bulb props included only if light is connected
        """
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
                'is_flowing': self.__is_flowing,
                'effect': self.__effect,
                'effect_props': self.__effect_props
            }
        return props

    def __save(self):
        """
        Saves database properties of a light
        """
        db.save_light({'ip': self.ip,
            'name': self.name,
            'is_default': self.is_default},
            _id=self.id
        )

    @property
    def ip(self):
        return self.__bulb._ip

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
    def name(self, new_name: str):
        """
        Sets light name, which is then saved in the database
        :param new_name: new light name
        """
        max_light_length = _lights_config['max_light_length']
        if len(new_name) > max_light_length:
            raise ValueError(f'Light name may have a maximum of {max_light_length} characters')
        self.__name = new_name
        self.__save()

    @property
    def is_default(self):
        return self.__is_default
    
    @is_default.setter
    def is_default(self, new_is_default: bool):
        """
        A 'default' light is one to which group actions apply.
        If set to False, it will only change state if called directly.
        :param new_is_default: whether light is default or not
        """
        self.__is_default = new_is_default
        self.__save()

    @property
    def brightness(self):
        return self.__brightness

    @brightness.setter
    def brightness(self, new_brightness: int):
        """
        Sets light brightness.
        :param new_brightness: brightness expressed as a number between 1 and 100.
        """
        if not 1 <= new_brightness <= 100:
            raise ValueError('Brightness must be between 1 and 100')
        self.__bulb.set_brightness(new_brightness)
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
        
        self.__bulb.set_rgb(**color_obj.rgb_dict)
        self.__color = color_obj
    

    @property
    def on(self):
        return self.__on
    
    @on.setter
    def on(self, new_on: bool):
        if new_on:
            self.__bulb.turn_on()
        else:
            self.__bulb.turn_off()
            self.__clear_effect()
        self.__on = new_on


    def set_effect(self, effect_name: str, effect_props: Dict):
        """
        Starts / stops a smart light effect.
        :param effect_name: effect to be shown. Must be an existing key in 'effects_map' or None, which indicates stop current effect
        :effect_props: properties as supported by individual effects. If unsupported prop is supplied, effect constructor will throw TypeError
        """
        try:
            if effect_name is None:
                self.__bulb.stop_flow()
                self.__clear_effect()
            else:
                effect = self.effects_map[effect_name](**effect_props)
                self.__bulb.start_flow(effect.get_flow())
                self.__is_flowing = True
                self.__effect = effect_name
                self.__effect_props = effect_props
        except TypeError as err:
            logging.error(err)
            raise ValueError('Props supplied to effect are incorrect')

    def __clear_effect(self):
        """
        Resets properties to indicate no effect is currently applied on a light
        """
        self.__is_flowing = False
        self.__effect = None
        self.__effect_props = {}

    def __implied_disconnected(self):
        """
        Invoked when behaviour of the light implies it is no longer connected, so was probably turned off
        Resets properties to the state they must be in if the light is truly turned off
        """
        self.__is_connected = False
        self.__clear_effect()

    def __setattr__(self, name, value):
        try:
            with self.__lock:
                try:
                    super(Light, self).__setattr__(name, value)
                except BulbException as err:
                    # bulb no longer online
                    logging.error(err)
                    self.__implied_disconnected()
                    raise err
        except AttributeError:
            # no lock yet
            super(Light, self).__setattr__(name, value)


def _create_light(db_data: Dict, is_connected: bool) -> Light:
    logging.info(f'Creating light with IP: {db_data["ip"]}')
    light = Light(**db_data, is_connected=is_connected)

    if is_connected:
        light.refresh_props()
    return light


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
            self.__lights = []
            self.__do_lights_discovery()
            self.__do_refresh_light_props()
            LightManager.__instance = self

    def instance():
        if LightManager.__instance is None:
            LightManager()
        return LightManager.__instance


    def __save_new_lights(bulb_info: List[Dict]):
        """
        Saves bulbs that are not yet in the database
        :param bulb_info: list of dictionaries, each representing information about an individual bulb, currently connected on the network
        """
        db_lights = db.get_lights()
        for bulb in bulb_info:
            if bulb['ip'] not in db_lights.distinct('ip'):
                db.save_new_light({
                    'ip': bulb['ip'],
                    'name': bulb['capabilities']['name'],
                    'is_default': False
                })

    def get_light_by_name(self, name):
        for light in self.__lights:
            if light.name == name.upper():
                return light
        return None

    def __get_light_by_ip(self, ip):
        for light in self.__lights:
            if light.ip == ip:
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
                    executor.submit(
                        _create_light, db_light, db_light['ip'] in [bulb['ip'] for bulb in connected_bulbs]
                        ).add_done_callback(
                            lambda future: self.__lights.append(future.result())
                            )
        thread = threading.Timer(_lights_config['discovery_interval'], self.__do_lights_discovery)
        thread.daemon = True
        thread.start()

    def __do_refresh_light_props(self):
        """
        Periodically, refreshes properties of lights.
        The requirement comes from that clients are not allowed to call 'get_properties' directly on a Bulb, which is
        the only way to know the true, current state, but there's a limit on direct bulb API calls per minute
        """
        for light in self.__lights:
            light.refresh_props()
        thread = threading.Timer(_lights_config['refresh_interval'], self.__do_refresh_light_props)
        thread.daemon = True
        thread.start()
        
