from yeelight import Bulb, Flow, discover_bulbs
from yeelight.transitions import *


def _initialize_lights():
    lights = []

    for instance in discover_bulbs():
        lights.append(Bulb(instance['ip']))

    return lights


class LightManager:

    def __init__(self):
        self.lights = _initialize_lights()
        self.default = self.get_light_by_name('lounge')

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

    def notify(self, status='info', *bulbs):
        if status == 'info':
            red, green, blue = 0, 0, 255
        elif status == 'ok':
            red, green, blue = 0, 255, 0
        elif status == 'warn':
            red, green, blue = 255, 0, 0
        else:
            raise KeyError

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


