import pytest


@pytest.fixture()
def get_color():
    from iot_app.iot.lights.color import Color
    return Color


def test_rgb_tuple(get_color):
    color = get_color(255, 0, 0)
    assert color.rgb_tuple == (255, 0, 0)


def test_rgb_dict(get_color):
    color = get_color(255, 255, 0)
    assert color.rgb_dict == {'red': 255, 'green': 255, 'blue': 0}


def test_rgb_int(get_color):
    color = get_color.from_rgb_int(16711935)
    assert color.rgb_tuple == (255, 0, 255)


def test_invalid_rgb_int(get_color):
    with pytest.raises(ValueError):
        get_color.from_rgb_int(16777216)


def test_hex(get_color):
    _hex = "#00ff00"
    color = get_color.from_hex(_hex)
    assert color.rgb_tuple == (0, 255, 0)
    assert color.hex == _hex


def test_invalid_hex(get_color):
    with pytest.raises(ValueError):
        get_color.from_hex("#00ff000")
