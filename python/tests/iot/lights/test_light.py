import pytest


@pytest.fixture()
def connected_light_and_bulb(bulb):
    from iot_app.iot.lights.light import Light
    light = Light('192.168.0.20', 'uuid123', 'light name', True, True)
    bulb.is_connected = True
    return light, bulb


@pytest.fixture()
def disconnected_light_and_bulb(bulb):
    from iot_app.iot.lights.light import Light
    light = Light('192.168.0.20', 'uuid123', 'light name', True, False)
    bulb.is_connected = False
    return light, bulb


invalid_colors_data = [
    True,
    False,
    None,
    {'some': 'dict'}]

offline_props = {
    'id': 'uuid123',
    'ip': '192.168.0.20',
    'is_default': True,
    'name': 'light name'
}

online_props = {
    'brightness': 50,
    'color': '#ff00ff',
    'effect': None,
    'effect_props': {},
    'is_flowing': False,
    'on': True
}

invalid_brightness = [
    -1,
    0,
    101,
    None,
    "str"
]


def test_dump_props_connected(connected_light_and_bulb):
    light, _ = connected_light_and_bulb
    # connected - should dump all props
    combined_props = {**offline_props, **online_props, 'is_connected': True}
    assert light.dump_props() == combined_props


def test_dump_props_disconnected(disconnected_light_and_bulb):
    light, _ = disconnected_light_and_bulb
    # disconnected - should dump offline props only
    assert light.dump_props() == {**offline_props, 'is_connected': False}


@pytest.mark.parametrize('effect_name', [None, 'disco', 'strobe'])
@pytest.mark.parametrize('effect_props', [None, {}, {'count': 5}])
def test_set_valid_effect_with_count(connected_light_and_bulb, effect_name, effect_props):
    light, _ = connected_light_and_bulb
    light.set_effect(effect_name, effect_props)

    should_effect_start = effect_name is not None
    expected_effect_props = {}
    if should_effect_start:
        if effect_props is not None:
            expected_effect_props = effect_props

    light_props = light.dump_props()
    assert light_props['effect'] == effect_name
    assert light_props['effect_props'] == expected_effect_props
    assert light_props['is_flowing'] is should_effect_start


@pytest.mark.parametrize('effect_name', [None, 'lsd', 'police', 'random'])
@pytest.mark.parametrize('effect_props', [
    None, {}, {'count': 5}, {'duration': 10}, {'count': 5, 'duration': 10}])
def test_set_valid_effect_with_count_and_duration(connected_light_and_bulb, effect_name, effect_props):
    light, _ = connected_light_and_bulb
    light.set_effect(effect_name, effect_props)
    light_props = light.dump_props()

    should_effect_start = effect_name is not None
    expected_effect_props = {}
    if should_effect_start:
        if effect_props is not None:
            expected_effect_props = effect_props

    assert light_props['effect'] == effect_name
    assert light_props['effect_props'] == expected_effect_props
    assert light_props['is_flowing'] is should_effect_start


@pytest.mark.parametrize('effect_name', [
    'disco', 'strobe', 'lsd', 'police', 'random'])
@pytest.mark.parametrize('effect_props', [{'unknown_prop': 'unknown_value'}])
def test_set_invalid_effect_prop(connected_light_and_bulb, effect_name, effect_props):
    from iot_app.iot.lights import LightException

    light, _ = connected_light_and_bulb
    with pytest.raises(LightException):
        light.set_effect(effect_name, effect_props)


def test_set_invalid_effect_name(connected_light_and_bulb):
    from iot_app.iot.lights import LightException

    light, _ = connected_light_and_bulb
    with pytest.raises(LightException):
        light.set_effect('no_such_effect')


def test_set_and_unset_effect(connected_light_and_bulb):
    light, _ = connected_light_and_bulb
    light.set_effect('disco')

    light_props = light.dump_props()
    assert light_props['effect'] == 'disco'
    assert light_props['effect_props'] == {}
    assert light_props['is_flowing'] is True

    light.set_effect(None)

    light_props = light.dump_props()
    assert light_props['effect'] is None
    assert light_props['effect_props'] == {}
    assert light_props['is_flowing'] is False


def test_set_effect_on_disconnected(disconnected_light_and_bulb):
    from iot_app.iot.lights import LightException
    light, _ = disconnected_light_and_bulb

    with pytest.raises(LightException):
        light.set_effect('disco')


def test_set_color_valid_hex(connected_light_and_bulb):
    light, _ = connected_light_and_bulb
    light.color = '#00aa3c'
    assert light.dump_props()['color'] == '#00aa3c'


def test_set_color_valid_rgb(connected_light_and_bulb):
    light, _ = connected_light_and_bulb
    light.color = (0, 170, 60)
    assert light.dump_props()['color'] == '#00aa3c'


def test_set_color_obj(connected_light_and_bulb):
    light, _ = connected_light_and_bulb

    from iot_app.iot.lights.color import Color
    color = Color.from_hex('#00aa3c')
    light.color = color
    assert light.dump_props()['color'] == '#00aa3c'


@pytest.mark.parametrize('bad_color', invalid_colors_data)
def test_set_color_invalid(connected_light_and_bulb, bad_color):
    light, _ = connected_light_and_bulb
    with pytest.raises(ValueError):
        light.color = bad_color


def test_set_valid_name(disconnected_light_and_bulb):
    light, bulb = disconnected_light_and_bulb

    new_name = 'Some light'
    assert light.name != new_name
    light.name = new_name
    assert light.name == new_name


def test_set_invalid_name(disconnected_light_and_bulb):
    light, _ = disconnected_light_and_bulb

    too_many_chars = ('x' * 33)
    with pytest.raises(ValueError):
        light.name = too_many_chars


def test_set_is_default(disconnected_light_and_bulb):
    light, _ = disconnected_light_and_bulb

    assert light.is_default is True

    light.is_default = False
    assert light.is_default is False

    light.is_default = True


def test_set_valid_brightness(connected_light_and_bulb):
    light, _ = connected_light_and_bulb

    assert light.brightness == 50

    light.brightness = 100
    assert light.brightness == 100


@pytest.mark.parametrize('bad_brightness', invalid_brightness)
def test_set_invalid_brightness(connected_light_and_bulb, bad_brightness):
    light, _ = connected_light_and_bulb

    with pytest.raises(Exception):
        light.brightness = bad_brightness


def test_disconnect_then_set_brightness(connected_light_and_bulb):
    light, bulb = connected_light_and_bulb
    from iot_app.iot.lights import LightException

    assert light.dump_props() == {**offline_props, **online_props, 'is_connected': True}

    bulb.is_connected = False

    with pytest.raises(LightException):
        light.brightness = 25

    assert light.dump_props() == {**offline_props, 'is_connected': False}


def test_turn_on_and_off(connected_light_and_bulb):
    light, _ = connected_light_and_bulb

    assert light.on is True

    light.on = False
    assert light.on is False

    light.on = True
    assert light.on is True

