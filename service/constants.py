"""Módulo 'constants' de georef-ar-api

Contiene variables con valores constantes.
"""

from flask import current_app

API_NAME = 'georef-ar-api'

MAX_RESULT_LEN = current_app.config['MAX_RESULT_LEN']
MAX_RESULT_WINDOW = current_app.config['MAX_RESULT_WINDOW']
MAX_BULK_LEN = current_app.config['MAX_BULK_LEN']
ES_MULTISEARCH_MAX_LEN = current_app.config.get('ES_MULTISEARCH_MAX_LEN',
                                                MAX_RESULT_LEN)
ES_TRACK_TOTAL_HITS = current_app.config.get('ES_TRACK_TOTAL_HITS')
ADDRESS_PARSER_CACHE_SIZE = current_app.config['ADDRESS_PARSER_CACHE_SIZE']

ISCT_DOOR_NUM_TOLERANCE_M = 50
BTWN_DOOR_NUM_TOLERANCE_M = 150
BTWN_DISTANCE_TOLERANCE_M = 200

MIN_AUTOCOMPLETE_CHARS = 4
DEFAULT_SEARCH_SIZE = 10
DEFAULT_FUZZINESS = 'AUTO:4,8'

STATE_ID_LEN = 2
DEPT_ID_LEN = 5
MUNI_ID_LEN = 6
CENSUS_LOCALITY_ID_LEN = 8
SETTLEMENT_ID_LEN = (8, 10)
LOCALITY_ID_LEN = (8, 10)
STREET_ID_LEN = 13
