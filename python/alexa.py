from flask import render_template
from flask_ask import question, statement
from web_assets import *
from lights import *
from isodate import parse_duration

IOT_ENV = {"temp": None, "humidity": None}


def welcome():
    card_title = render_template('card_title_pi')
    question_text = render_template('welcome')
    return question(question_text).standard_card(card_title, question_text, pi_img)


def climate_info(prop, warmth):
    card_title = render_template('card_title_pi')

    if warmth is prop is None:
        answer = render_template('temp_and_humidity').format(IOT_ENV['temp'], IOT_ENV['humidity'])
        return statement(answer).standard_card(card_title, answer, pi_img)

    if warmth is not None:
        answer = render_template('temp').format(IOT_ENV["temp"])
        return statement(answer).standard_card(card_title, answer, temp_img)

    if prop == 'humidity':
        card_img = humidity_img
        answer = render_template('humidity').format(IOT_ENV["humidity"])
    else:
        card_img = temp_img
        answer = render_template('temp').format(IOT_ENV["temp"])

    return statement(answer).standard_card(card_title, answer, card_img)


def start_disco(room):
    return LightAction(LightManager(), render_template('card_title_lights'), light_img).start_disco(room)


def stop_flow(room):
    return LightAction(LightManager(), render_template('card_title_lights'), light_img).stop_flow(room)


def start_fade(room, duration, off):
    return LightAction(LightManager(), render_template('card_title_lights'), light_img).start_fade(room, duration, off)


def stop_fade(room):
    return LightAction(LightManager(), render_template('card_title_lights'), light_img).stop_fade(room)


class LightAction:
    def __init__(self, light_manager: LightManager, card_title: str, card_img: str):
        self.light_manager = light_manager
        self.card_title = card_title
        self.card_img = card_img

    def start_disco(self, room):
        fail_stmt = self.__validate(room)
        if fail_stmt is not None:
            return fail_stmt

        if room is None:
            self.light_manager.start_disco()
            return self.__stmt_disco_ok()
        else:
            if room == 'all' or room == 'everywhere':
                self.light_manager.start_disco(*self.light_manager.get_all_lights())
                return self.__stmt_disco_ok()
            else:
                light = self.light_manager.get_light_by_name(room)
                self.light_manager.start_disco(light)
                return self.__stmt_disco_ok()

    def stop_flow(self, room):
        fail_stmt = self.__validate(room)
        if fail_stmt is not None:
            return fail_stmt

        if room is None or room == 'all' or room == 'everywhere':
            self.light_manager.stop_flow(*self.light_manager.get_all_lights())
            return self.__stmt_stopped_lights()
        else:
            light = self.light_manager.get_light_by_name(room)
            self.light_manager.stop_flow(light)
            return self.__stmt_stopped_lights()

    def start_fade(self, room, duration, off):
        fail_stmt = self.__validate(room)
        if fail_stmt is not None:
            return fail_stmt

        turn_off = off is not None

        if duration is not None:
            duration = int(parse_duration(duration).total_seconds())
        else:
            duration = 120  # default, in seconds

        if room is None:
            self.light_manager.fade(duration, turn_off)
            room = self.light_manager.get_default_room().lower()
            return self.__stmt_fade_ok(room, duration)
        else:
            if room == 'all' or room == 'everywhere':
                self.light_manager.fade(duration, turn_off, 5, *self.light_manager.get_all_lights())
                return self.__stmt_fade_ok(room, duration)
            else:
                light = self.light_manager.get_light_by_name(room)
                self.light_manager.fade(duration, turn_off, 5, light)
                return self.__stmt_fade_ok(room, duration)

    def stop_fade(self, room):
        fail_stmt = self.__validate(room)
        if fail_stmt is not None:
            return fail_stmt

        if room is None or room == 'all' or room == 'everywhere':
            self.light_manager.stop_fade(*self.light_manager.get_all_lights())
            return self.__stmt_fade_stopped(room)
        else:
            light = self.light_manager.get_light_by_name(room)
            self.light_manager.stop_fade(light)
            return self.__stmt_fade_stopped(room)

    def __card_disco_ok(self):
        return self.card_title, render_template('disco_lights_card'), self.card_img

    def __card_no_lights(self):
        return self.card_title, render_template('no_lights'), self.card_img

    def __card_no_such_light(self, light_name):
        return self.card_title, render_template('no_such_light').format(light_name), self.card_img

    def __card_stopped_lights(self):
        return self.card_title, render_template('disco_lights_stopped_card'), self.card_img

    def __card_fade_ok(self, room, duration):
        return self.card_title, render_template('fade_started_card').format(name=room, duration=duration), self.card_img

    def __card_fade_stopped(self, room):
        return self.card_title, render_template('fade_stopped_card').format(name=room)

    def __stmt_disco_ok(self):
        return statement(render_template('disco_lights')).standard_card(*self.__card_disco_ok())

    def __stmt_no_lights(self):
        return statement(render_template('no_lights')).standard_card(*self.__card_no_lights())

    def __stmt_no_such_light(self, light_name):
        return statement(render_template('no_such_light').format(
            light_name)).standard_card(*self.__card_no_such_light(light_name))

    def __stmt_stopped_lights(self):
        return statement('OK').standard_card(*self.__card_stopped_lights())

    def __stmt_fade_ok(self, room, duration):
        return statement(render_template('fade_started').format(
            name=room,
            duration=get_duration_str(duration))).standard_card(*self.__card_fade_ok(room, get_duration_str(duration)))

    def __stmt_fade_stopped(self, room):
        return statement('OK').standard_card(*self.__card_fade_stopped(room))

    def __validate(self, room):
        if len(self.light_manager.get_all_lights()) == 0:
            return self.__stmt_no_lights()

        if room == 'all' or room == 'everywhere':
            return None

        if room is None:
            light = self.light_manager.get_light_by_name(self.light_manager.get_default_room())
            if light is not None:
                return None
            return self.__stmt_no_such_light(self.light_manager.get_default_room())
        else:
            light = self.light_manager.get_light_by_name(room)
            if light is not None:
                return None
            else:
                return self.__stmt_no_such_light(room)


def get_duration_str(duration: int) -> str:
    if duration < 60:
        return '{seconds} seconds'.format(seconds=duration)

    if duration % 60 != 0:
        minutes = int(duration / 60)
        seconds = duration - (minutes * 60)
        return '{minutes} minutes and {seconds} seconds'.format(minutes=minutes, seconds=seconds)

    return '{minutes}'.format(minutes=int(duration / 60))
