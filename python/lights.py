from yeelight import Bulb, Flow, discover_bulbs
from yeelight.transitions import *
import threading


def _initialize_lights():
    lights = []

    for instance in discover_bulbs():
        lights.append(Bulb(instance['ip']))

    return lights


class Room:
    BEDROOM = 'BEDROOM'
    LOUNGE = 'LOUNGE'


class NotificationLevel:
    OK = 0, 255, 100
    INFO = 0, 150, 255
    WARNING = 255, 150, 0
    ERROR = 255, 0, 50


class LightManager:

    def __init__(self):
        self.lights = _initialize_lights()
        self.default = self.get_light_by_name(Room.LOUNGE)

    def get_light_by_name(self, name):
        for light in self.lights:
            if light.get_properties(['name']).get('name') == name:
                return light

        return None

    def start_disco(self, *bulbs):
        flow = Flow(count=0, transitions=disco())

        if len(bulbs) > 0:
            for bulb in bulbs:
                bulb.start_flow(flow)
        else:
            self.default.start_flow(flow)

    def notify(self, level=NotificationLevel.INFO, *bulbs):
        red, green, blue = level

        flow = Flow(count=3, transitions=pulse(red, green, blue))

        if len(bulbs) > 0:
            for bulb in bulbs:
                bulb.start_flow(flow)
        else:
            self.default.start_flow(flow)

    def stop_flow(self, *bulbs):
        if len(bulbs) > 0:
            for bulb in bulbs:
                bulb.stop_flow()
        else:
            self.default.stop_flow()

    def set_default(self, name):
        self.default = self.get_light_by_name(name)

    def fade(self, duration, turn_off=False, *bulbs):
        max_requests_per_minute = 60
        bulb_calls_per_iteration = 3
        max_iterations_per_minute = max_requests_per_minute / bulb_calls_per_iteration
        min_interval = 60 / max_iterations_per_minute  # 60 seconds

        if len(bulbs) == 0:
            bulbs = [self.default]

        for bulb in bulbs:
            current_props = bulb.get_properties(['bright', 'ct', 'rgb', 'flowing'])
            initial_brightness = int(current_props['bright'])
            interval = max(min_interval, duration / _get_total_fade_steps(initial_brightness))
            _fade(bulb, interval, current_props, turn_off)


def _fade(bulb, interval, props, turn_off):
        # if another request was made, abort task
        if props != bulb.get_properties(['bright', 'ct', 'rgb', 'flowing']):
            return

        power = props['power']
        brightness = int(props['bright'])

        if power == 'off':
            return
        if brightness <= 1:
            if turn_off:
                bulb.turn_off()
            return

        new_brightness = __get_decreased_brightness(brightness)
        bulb.set_brightness(new_brightness)

        props = bulb.get_properties(['bright', 'ct', 'rgb', 'flowing'])
        threading.Timer(interval, _fade, [bulb, interval, props, turn_off]).start()


def _get_total_fade_steps(initial_brightness):
    steps = 0
    brightness = initial_brightness

    while brightness > 1:
        steps += 1
        brightness = __get_decreased_brightness(brightness)

    return steps


def __get_decreased_brightness(brightness):
    min_brightness = 1
    max_brightness = 99
    diff = max(1, round(brightness / 10))

    return max(min_brightness, min((brightness - diff), max_brightness))
