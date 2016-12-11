#!/usr/bin/python
# -*- coding: utf-8 -*-
import utils
import os
import random

env_skill_id = os.environ['skill_id']


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
    except:
        previous_place = None

    # Dispatch to your skill's intent handlers
    if intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return end_game(intent, session_attributes)

    elif intent_name == "AMAZON.YesIntent":
        if previous_place == "set_difficulty_level":
            return start_game(intent, session_attributes)
        elif previous_place == "end_game":
            return play_again(intent, session_attributes)

    elif intent_name == "AMAZON.NoIntent":
        return end_game(intent, session_attributes)

    elif intent_name == "StartGame":
        return get_welcome_response(session_attributes)

    elif intent_name == "SetDifficulty":
        return set_difficulty(intent, session_attributes)

    elif intent_name == "NumericResponse":
        return handle_quiz_answer(intent, session_attributes)

    else:
        raise ValueError("Invalid intent")


# ----------------------------------------------------------------------------------
# Functions that control the skill's intent
# ----------------------------------------------------------------------------------
def get_welcome_response(session_attributes):
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    speech_output = "<speak>Willkommen bei Mathe Ass. Wähle zuerst einen Schwierigkeitsgrad von null bis sechs. Um zum Beispiel " \
                    "mit Schwierigkeitsgrad null zu starten, sage Schwierigkeitsgrad null.</speak>"
    repromt_text = "<speak>Das habe ich nicht verstanden. Wähle einen Schwierigkeitsgrad von null bis sechs indem du sagst Schwierigkeitsgrad, " \
                   "und dann eine Zahl zwischen null und sechs.</speak>"
    should_end_session = False
    session_attributes["previous_place"] = "welcome"

    return utils.build_response(session_attributes,
        utils.build_speech_with_repromt_response(speech_output, should_end_session, repromt_text))


# user wants to cancel or stop skill
def end_game(intent, session_attributes):
    session_attributes["previous_place"] = "end_game"
    speech_output = "<speak>Danke dass du Mathe Ass gespielt hast. Willst du nochmal spielen?</speak>"
    should_end_session = False

    return utils.build_response(session_attributes,
        utils.build_speech_response(speech_output, should_end_session))


def play_again(intent, session_attributes):
    pass


def set_difficulty(intent, session_attributes):
    if 'Number' in intent['slots']:
        session_attributes["previous_place"] = "set_difficulty_level"
        should_end_session = False
        difficulty = int(intent["slots"]["Number"]["value"])
        session_attributes["difficulty"] = difficulty
        if difficulty < 1 or difficulty > 5:
            speech_output = "<speak>Wähle einen Schwierigkeitsgrad von null bis sechs. Um zum Beispiel " \
                            "mit Schwierigkeitsgrad null zu starten, sage Schwierigkeitsgrad null.</speak>"
        else:
            session_attributes['difficulty'] = str(difficulty)
            speech_output = "<speak>Ok wir starten mit Schwierigkeitsgrad " + str(difficulty) + ". Willst du jetzt das Spiel starten?</speak>"

        return utils.build_response(session_attributes,
            utils.build_speech_response(speech_output, should_end_session))


def start_game(intent, session_attributes):
    session_attributes["previous_place"] = "in_game"
    session_attributes["correct"] = 0
    session_attributes["incorrect"] = 0
    difficulty = int(session_attributes['difficulty'])
    question = get_question(difficulty)
    session_attributes["last_question"] = question["text"]
    session_attributes["expected_result"] = question["result"]
    return utils.build_response(session_attributes,
        utils.build_speech_with_repromt_response(question["text"], False, question["text"]))


def handle_quiz_answer(intent, session_attributes):
    session_attributes["previous_place"] = "handle_answer"
    expected_result = session_attributes["expected_result"]
    spoken_result = int(intent["slots"]["Answer"]["value"])
    if spoken_result == expected_result:
        session_attributes["correct"] += 1
        correct_output = "Richtig, gut gemacht. Nächste Frage: "
    else:
        session_attributes["incorrect"] += 1
        correct_output = "Leider nicht richtig. Nächste Frage: "

    question = get_question(session_attributes["difficulty"])
    session_attributes["last_question"] = question["text"]
    session_attributes["expected_result"] = question["result"]
    return utils.build_response(session_attributes,
        utils.build_speech_with_repromt_response(question["text"], False, question["text"]))


# ------------------------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------------------------
def get_question(difficulty):
    level = levels[difficulty]
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
        "level": 0,
        "operations": [
            {
                "name": "add",
                "term1_low": 0,
                "term1_high": 6,
                "term2_low": 0,
                "term2_high": 6
            }
        ]
    },
    {
        "level": 1,
        "operations": [
            {
                "name": "add",
                "term1_low": 0,
                "term1_high": 10,
                "term2_low": 0,
                "term2_high": 10
            }
        ]
    },
    {
        "level": 2,
        "operations": [
            {
                "name": "add",
                "term1_low": 0,
                "term1_high": 10,
                "term2_low": 0,
                "term2_high": 10
            },
            {
                "name": "sub",
                "term1_low": 0,
                "term1_high": 10,
                "term2_low": 0,
                "term2_high": 10
            }
        ]
    },
    {
        "level": 3,
        "operations": [
            {
                "name": "add",
                "term1_low": 5,
                "term1_high": 15,
                "term2_low": 3,
                "term2_high": 10
            },
            {
                "name": "sub",
                "term1_low": 2,
                "term1_high": 20,
                "term2_low": 2,
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
                "term1_high": 25,
                "term2_low": 5,
                "term2_high": 20
            },
            {
                "name": "sub",
                "term1_low": 5,
                "term1_high": 30,
                "term2_low": 5,
                "term2_high": 20
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
                "term1_low": 2,
                "term1_high": 10,
                "term2_low": 2,
                "term2_high": 10
            },
            {
                "name": "div",
                "term1_low": 2,
                "term1_high": 30,
                "term2_low": 2,
                "term2_high": 10
            }
        ]
    }
]