from flask import Flask, request, render_template
from flask_ask import Ask, question, statement
from web_assets import *
from lights import *
from app import IOT_ENV # temporary solution


lm = LightManager()


def welcome():
    card_title = render_template('card_title')
    question_text = render_template('welcome')
    return question(question_text).standard_card(card_title, question_text, pi_img)


def climate_info(prop, warmth):
    card_title = render_template('card_title_pi')

    if warmth is prop is None:
        answer = render_template('temp_and_humidity').format(IOT_ENV['temp'], IOT_ENV['humidity'])
        return statement(answer).standard_card(card_title, answer, pi_img)

    if warmth is not None:
        answer = render_template('temp') % IOT_ENV["temp"]
        return statement(answer).standard_card(card_title, answer, temp_img)

    if prop == 'humidity':
        card_img = humidity_img
        answer = render_template('humidity').format(IOT_ENV["humidity"])
    else:
        card_img = temp_img
        answer = render_template('temp').format(IOT_ENV["temp"])

    return statement(answer).standard_card(card_title, answer, card_img)


def start_disco(room):
    card_title = render_template('card_title_lights')
    card_img = light_img
    answer_success = render_template('disco_lights')
    answer_fail = render_template('no_lights')

    if len(lm.get_all()) == 0:
        return statement(answer_fail).standard_card(card_title, 'No lights', card_img)

    if room is None:
        lm.start_disco()
        return statement(answer_success).standard_card(card_title, 'Disco', card_img)
    else:
        if room == 'all' or room == 'everywhere':
            lm.start_disco(lm.get_all())
            answer = render_template('disco_lights')
            return statement(answer).standard_card(card_title, 'Disco', card_img)
        else:
            light = lm.get_light_by_name(room)
            if light is not None:
                lm.start_disco(lm)
                return statement(answer_success).standard_card(card_title, 'Disco', card_img)
            else:
                return statement(answer_fail).standard_card(card_title, 'No lights', card_img)


def stop_flow(room):
    card_title = render_template('card_title_lights')
    card_img = light_img

    if room is None:
        lm.stop_flow()
        return "{}", 200
    else:
        if room == 'all' or room == 'everywhere':
            lm.stop_flow(lm.get_all())
            return "{}", 200
        else:
            light = lm.get_light_by_name(room)
            if light is not None:
                lm.stop_flow(light)
                return "{}", 200
            else:
                answer = render_template('no_such_light')
                return statement(answer).standard_card(card_title, 'Not found', card_img)
