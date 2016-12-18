#!/usr/bin/python
# -*- coding: utf-8 -*-
import utils
import os
import random

env_skill_id = os.environ['skill_id']

number_text = ["eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben"]
turns = 8
correct = ["Richtig, gut gemacht. ", "Korrekt. ", "Richtig. "]
incorrect = ["Leider nicht richtig. ", "Stimmt leider nicht. ", "Leider falsch. "]


# ----------------------------------------------------------------------------------
# Events triggered from AVS
# ----------------------------------------------------------------------------------
def lambda_handler(event, context):
    # only call function, if it is triggered from my own skill
    if event['session']['application']['applicationId'] != env_skill_id:
        raise ValueError("Invalid Application ID")

    print("All incoming Event Details: " + str(event))

    # Create two main objects from 'event'
    session = event['session']
    request_obj = event['request']

    # Session Attributes are used to track elements like current question details, last intent/function position, etc
    session_attributes = utils.load_session_attributes(session)
    print("Session Attributes: " + str(session_attributes))

    if request_obj['type'] == "LaunchRequest":
        return on_launch(request_obj, session_attributes)
    elif request_obj['type'] == "IntentRequest":
        return on_intent(request_obj, session_attributes)


def on_launch(launch_request, session_attributes):
    # Called when the user launches the skill without specifying what they want
    return get_welcome_response(session_attributes)


def on_intent(intent_request, session_attributes):
    # Called when the user specifies an intent for this skill
    print("Intent Request Name: " + intent_request['intent']['name'])
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    try:
        previous_place = session_attributes["previous_place"]
    except KeyError:
        previous_place = None

    # Dispatch to your skill's intent handlers
    if intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return exit_game(intent, session_attributes)

    elif intent_name == "AMAZON.YesIntent":
        if previous_place == "replay_question":
            return play_again(intent, session_attributes)
        else:
            return replay_last_question(intent, session_attributes)

    elif intent_name == "AMAZON.NoIntent":
        if previous_place == "replay_question":
            return exit_game(intent, session_attributes)
        else:
            return replay_last_question(intent, session_attributes)

    elif intent_name == "StartGame":
        if previous_place is None:
            return get_welcome_response(session_attributes)
        else:
            return replay_last_question(intent, session_attributes)

    elif intent_name == "SetDifficulty":
        if previous_place == "welcome" or previous_place == "play_again":
            return set_difficulty(intent, session_attributes)
        else:
            return replay_last_question(intent, session_attributes)

    elif intent_name == "NumericResponse":
        if previous_place == "set_difficulty_level" or previous_place == "handle_answer":
            return handle_quiz_answer(intent, session_attributes)
        else:
            return replay_last_question(intent, session_attributes)

    else:
        print("Invalid intent")
        return replay_last_question(intent, session_attributes)


# ----------------------------------------------------------------------------------
# Functions that control the skill's intent
# ----------------------------------------------------------------------------------
def get_welcome_response(session_attributes):
    session_attributes["previous_place"] = "welcome"
    should_end_session = False
    speech_output = "<speak>Willkommen bei Mathe Trainer. Wähle zuerst einen Schwierigkeitsgrad von eins bis sieben. Um zum Beispiel " \
                    "mit Schwierigkeitsgrad drei zu starten, sage, Schwierigkeitsgrad drei.</speak>"
    repromt_text = "<speak>So funktioniert das nicht. Du musst sagen, Schwierigkeitsgrad, und dann eine Zahl von eins bis sieben</speak>"

    session_attributes['last_question'] = repromt_text
    return utils.build_response(session_attributes,
        utils.build_speech_with_repromt_response(speech_output, should_end_session, repromt_text))


def set_difficulty(intent, session_attributes):
    session_attributes["previous_place"] = "set_difficulty_level"
    should_end_session = False
    difficulty = int(intent["slots"]["Number"]["value"])
    if difficulty < 1 or difficulty > 7:
        difficulty = 1
    session_attributes['difficulty'] = difficulty
    session_attributes["correct"] = 0
    session_attributes["incorrect"] = 0
    session_attributes["turns"] = 0
    new_question = get_question(difficulty)
    session_attributes["expected_result"] = new_question["result"]
    speech_output = "<speak>Ok, dann starten wir mit Schwierigkeitsgrad " + number_text[difficulty - 1] + ". " + new_question["text"] + ".</speak>"
    repromt_text = "<speak>" + new_question["text"] + "</speak>"
    print("Repromt Text:" + repromt_text)

    session_attributes['last_question'] = new_question["text"]
    return utils.build_response(session_attributes,
        utils.build_speech_with_repromt_response(speech_output, should_end_session, repromt_text))


def handle_quiz_answer(intent, session_attributes):
    should_end_session = False
    session_attributes["previous_place"] = "handle_answer"
    session_attributes["turns"] += 1
    expected_result = session_attributes["expected_result"]
    try:
        spoken_result = int(intent["slots"]["Answer"]["value"])
    except ValueError:
        spoken_result = -1  # user did not say a number (e.g. a word)

    new_question = get_question(session_attributes["difficulty"])
    session_attributes["expected_result"] = new_question["result"]
    if spoken_result == expected_result:
        session_attributes["correct"] += 1
        speech_part = random.choice(correct)
    else:
        session_attributes["incorrect"] += 1
        speech_part = random.choice(incorrect)

    if session_attributes["turns"] < turns:
        speech_part += "Nächste Frage: " + new_question["text"]
        repromt_text = "<speak>" + new_question["text"] + "</speak>"
    else:
        speech_part += "<break time='1s'/>Das Spiel ist zu Ende. Du hast "
        speech_part += str(session_attributes["correct"]) + " von " + str(turns) + " Fragen richtig beantwortet. "
        speech_part += "Willst du nochmal spielen?"
        repromt_text = "<speak>Willst du nochmal spielen?</speak>"
        session_attributes["previous_place"] = "replay_question"

    speech_output = "<speak>" + speech_part + "</speak>"

    session_attributes['last_question'] = repromt_text
    return utils.build_response(session_attributes,
        utils.build_speech_with_repromt_response(speech_output, should_end_session, repromt_text))


def exit_game(intent, session_attributes):
    speech_output = "<speak>Ok. Danke dass du Mathe Trainer gespielt hast. Bis bald.</speak>"
    session_attributes['last_question'] = speech_output
    return utils.build_response(session_attributes,
        utils.build_speech_response(speech_output, True))


def play_again(intent, session_attributes):
    session_attributes = dict()
    session_attributes["previous_place"] = "play_again"
    speech_output = "<speak>Ok, wir fangen wieder neu an: Wähle einen Schwierigkeitsgrad von eins bis sieben.</speak>"
    repromt_text = "<speak>Du musst sagen, Schwierigkeitsgrad, und dann eine Zahl von eins bis sieben.</speak>"
    should_end_session = False
    session_attributes['last_question'] = repromt_text
    return utils.build_response(session_attributes,
        utils.build_speech_with_repromt_response(speech_output, should_end_session, repromt_text))


def replay_last_question(intent, session_attributes):
    speech_output = session_attributes['last_question']
    repromt_text = session_attributes['last_question']
    return utils.build_response(session_attributes,
        utils.build_speech_with_repromt_response(speech_output, False, repromt_text))


# ------------------------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------------------------
def get_question(difficulty):
    level = levels[difficulty - 1]
    operation = random.choice(level["operations"])
    term1 = random.randint(operation["term1_low"], operation["term1_high"])
    term2 = random.randint(operation["term2_low"], operation["term2_high"])

    if operation["name"] == "add":
        result = term1 + term2
        question = "Was ist %s plus %s" % (term1, term2)
    if operation["name"] == "sub":
        # term1 must be greater
        if term1 < term2:
            temp = term1
            term1 = term2
            term2 = temp
        result = term1 - term2
        question = "Was is %s minus %s" % (term1, term2)
    if operation["name"] == "mult":
        result = term1 * term2
        question = "Was is %s mal %s" % (term1, term2)
    if operation["name"] == "div":
        while term1 % term2 != 0:
            term1 = random.randint(operation["term1_low"], operation["term1_high"])
            term2 = random.randint(operation["term2_low"], operation["term2_high"])
        result = term1 / term2
        question = "Was is %s geteilt durch %s" % (term1, term2)

    return {
        "text": question,
        "result": result
    }


levels = [
    {
        "level": 1,
        "operations": [
            {
                "name": "add",
                "term1_low": 1,
                "term1_high": 6,
                "term2_low": 1,
                "term2_high": 6
            }
        ]
    },
    {
        "level": 2,
        "operations": [
            {
                "name": "add",
                "term1_low": 2,
                "term1_high": 10,
                "term2_low": 2,
                "term2_high": 10
            }
        ]
    },
    {
        "level": 3,
        "operations": [
            {
                "name": "add",
                "term1_low": 4,
                "term1_high": 15,
                "term2_low": 4,
                "term2_high": 12
            },
            {
                "name": "sub",
                "term1_low": 5,
                "term1_high": 15,
                "term2_low": 3,
                "term2_high": 10
            }
        ]
    },
    {
        "level": 4,
        "operations": [
            {
                "name": "add",
                "term1_low": 5,
                "term1_high": 30,
                "term2_low": 4,
                "term2_high": 15
            },
            {
                "name": "sub",
                "term1_low": 5,
                "term1_high": 25,
                "term2_low": 3,
                "term2_high": 10
            }
        ]
    },
    {
        "level": 5,
        "operations": [
            {
                "name": "mult",
                "term1_low": 2,
                "term1_high": 10,
                "term2_low": 2,
                "term2_high": 10
            }
        ]
    },
    {
        "level": 6,
        "operations": [
            {
                "name": "mult",
                "term1_low": 3,
                "term1_high": 10,
                "term2_low": 3,
                "term2_high": 10
            },
            {
                "name": "div",
                "term1_low": 9,
                "term1_high": 40,
                "term2_low": 3,
                "term2_high": 9
            }
        ]
    },
    {
        "level": 7,
        "operations": [
            {
                "name": "mult",
                "term1_low": 3,
                "term1_high": 10,
                "term2_low": 3,
                "term2_high": 12
            },
            {
                "name": "div",
                "term1_low": 9,
                "term1_high": 60,
                "term2_low": 3,
                "term2_high": 15
            }
        ]
    }
]
