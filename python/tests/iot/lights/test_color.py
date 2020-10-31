import pytest

valid_colors_data = [
    # rgb, hex equivalent
    ((100, 168, 50), '#64a832'),
    ((109, 50, 168), '#6d32a8'),
    ((209, 50, 119), '#d13277'),
    ((58, 50, 209), '#3a32d1'),
    ((0, 170, 60), '#00aa3c')
]

invalid_constructor_args = [
    ('a', 'b', 'c'),
    (0, 'a', '255'),
    (0, 0, True),
    (255, 255, 256),
    (-1, 0, 0),
    (None, None, None),
    (True, True, True),
    (False, False, False)
]

invalid_hex_data = [
    None,
    True,
    False,
    {'some': 'dict'},
    '!@#$%^',
    '#fzvcdfd'
]


@pytest.fixture()
def color_class():
    from iot_app.iot.lights.color import Color
    return Color


@pytest.mark.parametrize('rgb, _hex', valid_colors_data)
def test_valid_constructor_args(color_class, rgb, _hex):
    r, g, b = rgb
    color = color_class(r, g, b)
    assert color.rgb_tuple == rgb
    assert color.rgb_dict == {
        'red': r,
        'green': g,
        'blue': b
    }
    assert color.hex == _hex


@pytest.mark.parametrize('invalid_color', invalid_constructor_args)
def test_invalid_constructor_args(color_class, invalid_color):
    with pytest.raises(ValueError):
        color_class(*invalid_color)


def test_from_valid_int(color_class):
    color = color_class.from_rgb_int(16711935)
    assert color.rgb_tuple == (255, 0, 255)


def test_invalid_rgb_int(color_class):
    with pytest.raises(ValueError):
        color_class.from_rgb_int(16777216)


@pytest.mark.parametrize('rgb, _hex', valid_colors_data)
def test_from_valid_hex(color_class, rgb, _hex):
    color = color_class.from_hex(_hex)
    assert color.hex == _hex
    assert color.rgb_tuple == rgb
    r, g, b = rgb
    assert color.rgb_dict == {
        'red': r,
        'green': g,
        'blue': b
    }


@pytest.mark.parametrize('invalid_color', invalid_hex_data)
def test_from_invalid_hex(color_class, invalid_color):
    with pytest.raises(ValueError):
        color_class.from_hex(invalid_color)

