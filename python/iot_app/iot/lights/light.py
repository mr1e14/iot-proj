from iot_app.logger import get_logger
from iot_app.config import config
from iot_app.iot.lights.color import Color

from yeelight import Bulb, Flow, BulbException
from yeelight.transitions import *
from typing import Dict, Optional

import iot_app.db.lights as db

import threading
import time

logging = get_logger(__name__)

_lights_config = config['lights']


class LightException(Exception):
    """Exception raised due to failed operations on lights"""


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


class Light:
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
        logging.info(f'Creating light with IP: {ip}')
        self.__bulb = Bulb(ip, auto_on=True)
        self.__ip = ip
        self.__id = _id
        self.__name = name
        self.__is_default = is_default
        self.__is_connected = is_connected
        self.__brightness = 0
        self.__on = False
        self.__color = None
        self.__is_flowing = False
        self.__effect = None
        self.__effect_props = {}
        self.__lock = threading.RLock()

        if is_connected:
            self.__refresh_props()
        refresh_thread = threading.Thread(target=self.__do_refresh_light_props)
        refresh_thread.daemon = True
        refresh_thread.start()

    def dump_props(self) -> Dict:
        """
        Create a dictionary of light props. Bulb props included only if light is connected
        :return: dictionary of properties
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
        return self.__ip

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
        try:
            self.__bulb.set_brightness(new_brightness)
        except BulbException as err:
            logging.error(err)
            self.__handle_connection_failure()
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

        if isinstance(new_color, Color):
            color_obj = new_color
        elif isinstance(new_color, str):
            color_obj = Color.from_hex(new_color)
        else:
            color_obj = Color(*new_color)

        try:
            self.__bulb.set_rgb(**color_obj.rgb_dict)
        except BulbException as err:
            logging.error(err)
            self.__handle_connection_failure()
        self.__color = color_obj

    @property
    def on(self):
        return self.__on

    @on.setter
    def on(self, new_on: bool):
        try:
            if new_on:
                self.__bulb.turn_on()
            else:
                self.__bulb.turn_off()
                self.__clear_effect()
        except BulbException as err:
            logging.error(err)
            self.__handle_connection_failure()
        self.__on = new_on

    def set_effect(self, effect_name: str or None, effect_props: Optional[Dict] = None):
        """
        Starts / stops a smart light effect.
        :param effect_name: effect to be shown. Must be an existing key in 'effects_map' or None
        None effect_name indicates stop current effect
        :param effect_props: properties as supported by individual effects. If unsupported prop is supplied, effect
        constructor will throw TypeError
        """
        if effect_props is None:
            effect_props = {}
        try:
            if effect_name is None:
                self.__bulb.stop_flow()
                self.__clear_effect()
            else:
                effect_class = self.effects_map.get(effect_name)
                if effect_class is None:
                    raise LightException(f'No such effect: {effect_name}')
                try:
                    effect = effect_class(**effect_props)
                    self.__bulb.start_flow(effect.get_flow())
                    self.__is_flowing = True
                    self.__effect = effect_name
                    self.__effect_props = effect_props
                except TypeError as err:
                    logging.error(err)
                    raise LightException('Props supplied to effect are incorrect')
        except BulbException as err:
            logging.error(err)
            self.__handle_connection_failure()

    def __clear_effect(self):
        """
        Resets properties to indicate no effect is currently applied on a light
        """
        self.__is_flowing = False
        self.__effect = None
        self.__effect_props = {}

    def __clear_connection_props(self):
        """Resets properties to the state they must be in if the light is turned off """
        self.__is_connected = False
        self.__clear_effect()

    def __handle_connection_failure(self):
        """
        Invoked when smart bulb failed to perform requested operation
        """
        self.__clear_connection_props()
        raise LightException(f"Cannot connect to the smart bulb with IP: {self.ip}")

    def __refresh_props(self):
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
            except BulbException:
                self.__clear_connection_props()

    def __do_refresh_light_props(self):
        """
        Periodically, refreshes properties of this light.
        The requirement comes from that clients are not allowed to call 'get_properties' directly on a Bulb, which is
        the only way to know the true, current state, but there's a limit on direct bulb API calls per minute
        """
        while True:
            time.sleep(_lights_config['refresh_interval'])
            self.__refresh_props()

    def __setattr__(self, name, value):
        try:
            with self.__lock:
                super(Light, self).__setattr__(name, value)
        except AttributeError:
            # no lock yet
            super(Light, self).__setattr__(name, value)
