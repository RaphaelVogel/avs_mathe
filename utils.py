#!/usr/bin/python
# -*- coding: utf-8 -*-


# ----------------------------------------------------------------------------------
# Create Response helper functions
# ----------------------------------------------------------------------------------
def build_speech_response(speech_output, should_end_session):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': speech_output
        },
        'shouldEndSession': should_end_session
    }


def build_card_response(title, card_output, should_end_session):
    return {
        'card': {
            'type': 'Simple',
            'title': title,
            'content': card_output
        },
        'shouldEndSession': should_end_session
    }


def build_speech_and_card_response(speech_output, title, card_output, should_end_session):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': speech_output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': card_output
        },
        'shouldEndSession': should_end_session
    }


def build_speech_with_repromt_response(speech_output, should_end_session, repromt_text):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': speech_output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': repromt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# ----------------------------------------------------------------------------------
# Load session attributes
# ----------------------------------------------------------------------------------
def load_session_attributes(session):
    # Determine current session_attributes
    try:
        # Try to pull from existing session
        session_attributes = session["attributes"]
    except Exception:
        session_attributes = {}

    return session_attributes

