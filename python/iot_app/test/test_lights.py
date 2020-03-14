from unittest import main, mock, TestCase
import sys, time

win32api_module = mock.MagicMock()
sys.modules['win32api'] = win32api_module
import iot_app.iot.lights as lights
from yeelight.transitions import RGBTransition


class MockBulb:

    def __init__(self, ip, name):
        self.props = {'ip': ip, 'name': name, 'bright': 50, 'ct': 6500, 'rgb': 256, 'power': 'on'}
        self.start_flow_count = 0
        self.stop_flow_count = 0
        self.flow_called_with = None

    def get_properties(self, keys):
        props = {}
        for key in keys:
            props[key] = self.props[key]
        return props

    def start_flow(self, flow):
        self.flow_called_with = flow
        self.start_flow_count += 1

    def stop_flow(self):
        self.stop_flow_count += 1

    def set_brightness(self, brightness):
        self.props['bright'] = max(1, round(brightness))

    def turn_off(self):
        self.props['power'] = 'off'


def _initialize_lights():
    return [MockBulb('192.168.0.55', 'bedroom'), MockBulb('192.168.0.58', 'lounge')]


class LightsTest(TestCase):

    def setUp(self):
        with mock.patch('iot_app.iot.lights._initialize_lights', _initialize_lights):
            self.light_manager = lights.LightManager()
            self.default_bulb = self.light_manager.get_light_by_name(self.light_manager.get_default_room())

    def test_start_disco_on_default(self):
        # Exercise
        self.light_manager.start_disco()

        # Verify
        assert self.default_bulb.start_flow_count == 1

    def test_start_disco_given_bulb(self):
        # Setup
        mock_bulb = MockBulb('192.168.0.15', 'kitchen')

        # Exercise
        self.light_manager.start_disco(mock_bulb)

        # Verify
        assert mock_bulb.start_flow_count == 1
        assert self.default_bulb.start_flow_count == 0

    def test_start_disco_given_multiple_bulbs(self):
        # Setup
        mock_bulb1 = MockBulb('192.168.0.15', 'kitchen')
        mock_bulb2 = MockBulb('192.168.0.16', 'porch')

        # Exercise
        self.light_manager.start_disco(mock_bulb1, mock_bulb2, self.default_bulb)

        # Verify
        assert mock_bulb1.start_flow_count == 1
        assert mock_bulb2.start_flow_count == 1
        assert self.default_bulb.start_flow_count == 1

    def test_start_disco_on_corrupt_bulb(self):
        # Exercise / Verify
        with self.assertRaises(AttributeError):
            self.light_manager.start_disco(None)

    def test_stop_flow_on_default(self):
        # Exercise
        self.light_manager.stop_flow()

        # Verify
        assert self.default_bulb.stop_flow_count == 1

    def test_stop_flow_given_bulb(self):
        # Setup
        mock_bulb = MockBulb('192.168.0.15', 'kitchen')

        # Exercise
        self.light_manager.stop_flow(mock_bulb)

        # Verify
        assert mock_bulb.stop_flow_count == 1
        assert self.default_bulb.stop_flow_count == 0

    def test_stop_flow_given_multiple_bulbs(self):
        # Setup
        mock_bulb1 = MockBulb('192.168.0.15', 'kitchen')
        mock_bulb2 = MockBulb('192.168.0.16', 'porch')

        # Exercise
        self.light_manager.stop_flow(mock_bulb1, mock_bulb2, self.default_bulb)

        # Verify
        assert mock_bulb1.stop_flow_count == 1
        assert mock_bulb2.stop_flow_count == 1
        assert self.default_bulb.stop_flow_count == 1

    def test_notify_on_defaults(self):
        # Setup
        expected_rgb_transition = RGBTransition(0, 150, 255, 400)

        # Exercise
        self.light_manager.notify()

        # Verify
        assert self.default_bulb.start_flow_count == 1
        assert self.default_bulb.flow_called_with.count == 3
        for transition in self.default_bulb.flow_called_with.transitions:
            assert transition.red == expected_rgb_transition.red
            assert transition.green == expected_rgb_transition.green
            assert transition.blue == expected_rgb_transition.blue
            assert transition.duration == expected_rgb_transition.duration

    def test_notify_warning_level(self):
        # Setup
        expected_rgb_transition = RGBTransition(255, 150, 0, 400)

        # Exercise
        self.light_manager.notify(lights.NotificationLevel.WARNING)

        # Verify
        assert self.default_bulb.start_flow_count == 1
        assert self.default_bulb.flow_called_with.count == 3
        for transition in self.default_bulb.flow_called_with.transitions:
            assert transition.red == expected_rgb_transition.red
            assert transition.green == expected_rgb_transition.green
            assert transition.blue == expected_rgb_transition.blue
            assert transition.duration == expected_rgb_transition.duration

    def test_notify_error_level(self):
        # Setup
        expected_rgb_transition = RGBTransition(255, 0, 50, 400)

        # Exercise
        self.light_manager.notify(lights.NotificationLevel.ERROR)

        # Verify
        assert self.default_bulb.start_flow_count == 1
        assert self.default_bulb.flow_called_with.count == 3
        for transition in self.default_bulb.flow_called_with.transitions:
            assert transition.red == expected_rgb_transition.red
            assert transition.green == expected_rgb_transition.green
            assert transition.blue == expected_rgb_transition.blue
            assert transition.duration == expected_rgb_transition.duration

    def test_notify_ok_level(self):
        # Setup
        expected_rgb_transition = RGBTransition(0, 255, 100, 400)

        # Exercise
        self.light_manager.notify(lights.NotificationLevel.OK)

        # Verify
        assert self.default_bulb.start_flow_count == 1
        assert self.default_bulb.flow_called_with.count == 3
        for transition in self.default_bulb.flow_called_with.transitions:
            assert transition.red == expected_rgb_transition.red
            assert transition.green == expected_rgb_transition.green
            assert transition.blue == expected_rgb_transition.blue
            assert transition.duration == expected_rgb_transition.duration

    def test_notify_given_multiple_bulbs(self):
        # Setup
        mock_bulb1 = MockBulb('192.168.0.15', 'kitchen')
        mock_bulb2 = MockBulb('192.168.0.16', 'porch')
        expected_rgb_transition = RGBTransition(255, 150, 0, 400)

        # Exercise
        self.light_manager.notify(lights.NotificationLevel.WARNING, mock_bulb1, mock_bulb2)

        # Verify
        for bulb in [mock_bulb1, mock_bulb2]:
            assert bulb.start_flow_count == 1
            assert bulb.flow_called_with.count == 3

            for transition in bulb.flow_called_with.transitions:
                assert transition.red == expected_rgb_transition.red
                assert transition.green == expected_rgb_transition.green
                assert transition.blue == expected_rgb_transition.blue
                assert transition.duration == expected_rgb_transition.duration

    def test_set_default_room_exists(self):
        # Verify initial state
        assert 'LOUNGE' == self.light_manager.get_default_room()

        # Exercise
        self.light_manager.set_default('bedroom')

        # Verify
        assert 'bedroom' == self.light_manager.get_default_room()

    def test_set_default_no_such_room(self):
        # Verify initial state
        assert 'LOUNGE' == self.light_manager.get_default_room()

        # Exercise
        self.light_manager.set_default('porch')

        # Verify
        assert 'LOUNGE' == self.light_manager.get_default_room()

    def test_fade_on_defaults(self):
        # Setup
        self.default_bulb.set_brightness(100)
        fade_duration = 3

        # Exercise
        self.light_manager.fade(fade_duration)
        time.sleep(fade_duration + 0.1)

        # Verify
        assert self.default_bulb.get_properties(['power'])['power'] == 'on'
        assert self.default_bulb.get_properties(['bright'])['bright'] == 1

    def test_fade_and_turn_off(self):
        # Setup
        self.default_bulb.set_brightness(41)
        fade_duration = 3

        # Exercise
        self.light_manager.fade(duration=fade_duration, turn_off=True)
        time.sleep(fade_duration + 0.1)

        # Verify
        assert self.default_bulb.get_properties(['power'])['power'] == 'off'
        assert self.default_bulb.get_properties(['bright'])['bright'] == 1

    def test_fade_interrupted(self):
        # Setup
        self.default_bulb.set_brightness(100)
        fade_duration = 4
        new_requested_brightness = 60

        # Exercise
        self.light_manager.fade(duration=fade_duration, turn_off=True)
        time.sleep(2.1)
        self.default_bulb.set_brightness(new_requested_brightness)
        time.sleep(2)

        # Verify
        assert self.default_bulb.get_properties(['power'])['power'] == 'on'
        assert self.default_bulb.get_properties(['bright'])['bright'] == 60

    if __name__ == '__main__':
        main()
