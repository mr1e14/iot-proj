import pytest


@pytest.fixture()
def bulb(monkeypatch):
    from yeelight import BulbException

    class MockBulb:
        def __init__(self):
            self.__ip = ''
            self.__auto_on = False
            # connected by default
            self.__bulb_properties = {
                'bright': 50,
                'rgb': 16711935,
                'flowing': 0,
                'power': 'on'
            }
            self.is_connected = True

        def set_ip(self, ip):
            self.__ip = ip

        def get_properties(self):
            if not self.is_connected:
                raise BulbException('Disconnected')
            return self.__bulb_properties

        def start_flow(self, *args):
            if not self.is_connected:
                raise BulbException('Disconnected')

        def stop_flow(self):
            if not self.is_connected:
                raise BulbException('Disconnected')

        def set_rgb(self, **kwargs):
            if not self.is_connected:
                raise BulbException('Disconnected')

    mock_bulb = MockBulb()

    def get_bulb(ip, *args, **kwargs):
        mock_bulb.set_ip(ip)
        return mock_bulb

    monkeypatch.setattr('iot_app.iot.lights.light.Bulb', get_bulb)
    return mock_bulb


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
