from tornado.options import define

import json

# Defines
define("port", default=8888, help="run on the given port", type=int)
define("debug_mode", default=True, help="run server in debug mode", type=bool)

# Error Message
ERROR_INVALID_MESSAGE = json.dumps({'command': 'error',
                                    'error_message': 'Invalid Message'})
ERROR_GAME_NOT_FOUND = json.dumps({'command': 'error',
                                   'error_message': 'Game not found'})

WON_OUTCOME = 'won'
LOST_OUTCOME = 'lost'
LEFT_OUTCOME = 'left'
DRAW_OUTCOME = 'draw'
TURN_OUTCOME = 'turn'
WAIT_OUTCOME = 'wait'

ROW_LENGTH = 3
COL_LENGTH = 3
