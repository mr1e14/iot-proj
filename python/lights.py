from yeelight import Bulb, Flow, discover_bulbs, BulbException
from yeelight.transitions import *
import threading
import logging
from os.path import join, dirname

logs_dir = join(dirname(__file__), 'logs')
logging.basicConfig(filename=join(logs_dir, 'lights.log'), format='%(asctime)s %(message)s', level=logging.INFO)


def _initialize_lights():
    logging.info('Initializing lights')
    lights = []

    for instance in discover_bulbs():
        lights.append(Bulb(instance['ip']))

    logging.info('Found {} lights'.format(len(lights)))
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

    def __init__(self, default_room=Room.BEDROOM):
        self.__lights = _initialize_lights()
        self.__default_room = default_room
        self.__default = self.get_light_by_name(default_room)

    def get_light_by_name(self, name):
        for light in self.__lights:
            if light.get_properties(['name']).get('name').upper() == name.upper():
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
        logging.info('Flashing notification ({})'.format(level))

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
        light = self.get_light_by_name(name)
        if light is not None:
            self.__default = self.get_light_by_name(name)
            logging.info('Set new default light to {}'.format(name))
        else:
            logging.warning('Default not set. No such light: '.format(name))

    def get_all_lights(self):
        return self.__lights

    def get_default_room(self):
        return self.__default_room

    def stop_fade(self, *bulbs):
        logging.info('Aborting fade on user request')

        if len(bulbs) == 0:
            bulbs = [self.__default]

        #  fade effect is aborted if any change is made on the bulb
        for bulb in bulbs:
            current_brightness = int(bulb.get_properties(['bright']).get('bright'))
            bulb.set_brightness(current_brightness + 1)

    def fade(self, duration, turn_off=False, retries=5, *bulbs):
        logging.info('Fade started. Duration = {0}, turn_off={1}'.format(duration, turn_off))

        max_requests_per_minute = 60
        bulb_calls_per_step = 3
        max_steps_per_minute = max_requests_per_minute / bulb_calls_per_step

        min_interval = 1
        max_steps = _get_max_steps(duration, max_steps_per_minute)

        if len(bulbs) == 0:
            bulbs = [self.__default]

        for bulb in bulbs:
            current_props = bulb.get_properties(_get_required_props())
            initial_brightness = int(current_props['bright'])

            if duration <= max_steps_per_minute:
                interval = min_interval
                step = initial_brightness / interval
            else:
                interval = duration / max_steps
                step = initial_brightness / max_steps

            logging.info('Interval set to {}'.format(interval))

            _fade(bulb, interval, step, initial_brightness, current_props, turn_off, retries)


def _fade(bulb, interval, step, brightness, props, turn_off, retries, retry_delay=15):
        error_msg = 'Error occurred in __fade: {}'

        # if another request was made, abort task
        try:
            if props != bulb.get_properties(_get_required_props()):
                logging.info('Another request was made. Aborting fade.')
                return
        except BulbException as err:
            #  BulbException is fine - connection could be temporarily down
            logging.error(error_msg.format(err))
            if retries > 0:
                logging.info('Retrying. Attempts left: {}'.format(retries))
                threading.Timer(
                    retry_delay, _fade, [bulb, interval, step, brightness, props, turn_off, retries-1]).start()
                return

        power = props['power']

        if power == 'off':
            return
        if brightness <= 1:
            if turn_off:
                bulb.turn_off()
            return

        new_brightness = brightness - step
        updated_brightness = False
        try:
            bulb.set_brightness(round(new_brightness))
            updated_brightness = True
            props = bulb.get_properties(_get_required_props())
        except BulbException as err:
            logging.error(error_msg.format(err))

            if retries > 0:
                logging.info('Retrying. Attempts left: {}'.format(retries))
                if updated_brightness:
                    props['bright'] = str(round(new_brightness))
                    threading.Timer(
                        retry_delay, _fade, [bulb, interval, step, new_brightness, props, turn_off, retries-1]).start()
                else:
                    threading.Timer(
                        retry_delay, _fade,
                        [bulb, interval, step, brightness, props, turn_off, retries - 1]).start()
                return

        logging.info('Fade step. New brightness: {}'.format(new_brightness))

        threading.Timer(interval, _fade, [bulb, interval, step, new_brightness, props, turn_off, retries-1]).start()


def _get_max_steps(duration, max_steps_per_minute):
    return max_steps_per_minute * (1 + int(duration / 60))


def _get_required_props():
    return ['bright', 'ct', 'rgb', 'flowing', 'power']

