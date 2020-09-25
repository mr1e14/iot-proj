from iot_app.iot.lights.color import Color

import pytest


def test_rgb_tuple():
    color = Color(255, 0, 0)
    assert color.rgb_tuple == (255, 0, 0)


def test_rgb_dict():
    color = Color(255, 255, 0)
    assert color.rgb_dict == {'red': 255, 'green': 255, 'blue': 0}


def test_rgb_int():
    color = Color.from_rgb_int(16711935)
    assert color.rgb_tuple == (255, 0, 255)


def test_invalid_rgb_int():
    with pytest.raises(ValueError):
        Color.from_rgb_int(16777216)


def test_hex():
    _hex = "#00ff00"
    color = Color.from_hex(_hex)
    assert color.rgb_tuple == (0, 255, 0)
    assert color.hex == _hex


def test_invalid_hex():
    with pytest.raises(ValueError):
        Color.from_hex("#00ff000")
