from __future__ import annotations

from iot_app.logger import get_logger

from webcolors import hex_to_rgb, rgb_to_hex, normalize_hex
from typing import Dict, Tuple

logging = get_logger(__name__)


class Color:
    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue

    @staticmethod
    def from_rgb_int(rgb_int: int) -> Color:
        if rgb_int > 16777215 or rgb_int < 0:
            raise ValueError(f"Invalid RGB int value: {rgb_int}")
        blue = rgb_int & 255
        green = (rgb_int >> 8) & 255
        red = (rgb_int >> 16) & 255
        return Color(red=red, green=green, blue=blue)

    @staticmethod
    def from_hex(_hex: str) -> Color:
        try:
            normalized_hex = normalize_hex(_hex)
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
    def rgb_tuple(self) -> Tuple:
        return self.red, self.green, self.blue

    @property
    def hex(self) -> str:
        return rgb_to_hex(self.rgb_tuple)