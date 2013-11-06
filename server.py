# Tornado Imports
import tornado.ioloop
import tornado.httpserver
import tornado.options
import tornado.websocket
import tornado.web

from tornado.options import options

# Standard Library Imports
import json

# Import Constants
import constants


class Player:

    def __init__(self, name, socket, character):
        self.name = name
        self.socket = socket
        self.character = character

    def __str__(self):
        ret = "Player("
        ret += str(self.name) + ","
        ret += str(self.socket) + ","
        ret += str(self.character) + ")"
        return ret


class Game:

    def __init__(self, player1, player2, index):
        self.player1 = player1
        self.player2 = player2
        self.gameState = [["", "", ""], ["", "", ""], ["", "", ""]]
        self.gameIndex = index

    def __str__(self):
        ret = "Game("
        ret += str(self.player1) + ","
        ret += str(self.player2) + ","
        ret += str(self.gameState) + ","
        ret += str(self.gameIndex)
        ret += ")"
        return ret

    def startGame(self):

        # Send message to the players to start game
        self.player1.socket.write_message(json.dumps({
            'command': 'start',
            'player1Name': self.player1.name,
            'player2Name': self.player2.name,
            'gameState': self.gameState,
            'turn': 'Y',
            'character': self.player1.character
        }))

        self.player2.socket.write_message(json.dumps({
            'command': 'start',
            'player1Name': self.player1.name,
            'player2Name': self.player2.name,
            'gameState': self.gameState,
            'turn': 'N',
            'character': self.player2.character
        }))

    def makeMove(self, row, column, socket):

        # This function makes a change to the game state
        # when the player makes a move
        currentPlayerOutcome = constants.WAIT_OUTCOME
        otherPlayerOutcome = constants.TURN_OUTCOME

        currentPlayer, otherPlayer = self.whichPlayer(socket)
        currentCharacter = currentPlayer.character

        # Validate Move in game
        if self.gameState[row][column] == "":
            self.gameState[row][column] = currentCharacter
        else:
            # Invalid move let the player move again
            currentPlayerOutcome = constants.TURN_OUTCOME
            otherPlayerOutcome = constants.WAIT_OUTCOME

        # Check if game is won
        if self.isGameWon(row, column, currentCharacter):
            # If game is won then send victory messages
            currentPlayerOutcome = constants.WON_OUTCOME
            otherPlayerOutcome = constants.LOST_OUTCOME

            self.deleteGame(socket.application)
        else:
            # Check if game is a draw
            if self.isGameDraw():
                currentPlayerOutcome = constants.DRAW_OUTCOME
                otherPlayerOutcome = constants.DRAW_OUTCOME

        # Send move confirmation to player
        currentPlayer.socket.write_message(json.dumps({
            'command': 'move',
            'gameState': self.gameState,
            'outcome': currentPlayerOutcome
        }))

        # Send message to other player with move
        otherPlayer.socket.write_message(json.dumps({
            'command': 'move',
            'gameState': self.gameState,
            'outcome': otherPlayerOutcome
        }))

    def playerQuit(self, socket):
        currentPlayer, otherPlayer = self.whichPlayer(socket)

        # Send message to the other player
        otherPlayer.socket.write_message(json.dumps({
            'command': 'move',
            'gameState': self.gameState,
            'outcome': constants.LEFT_OUTCOME
        }))

         # Delete Game
        self.deleteGame(socket.application)

    def isGameWon(self, row, column, character):

        """ This function checks if the current player won
            the game """

        wonFlag = True

        # Check the column
        for i in range(0, constants.ROW_LENGTH):
            if self.gameState[i][column] != character:
                wonFlag = False
                break

        # Check the row
        if not wonFlag:

            wonFlag = True

            for i in range(0, constants.COL_LENGTH):
                if self.gameState[row][i] != character:
                    wonFlag = False
                    break

            # Check the first diagonal
            if not wonFlag:

                wonFlag = True

                for i in range(0, constants.COL_LENGTH):
                    if self.gameState[i][i] != character:
                        wonFlag = False
                        break

                # Check the second diagonal
                if not wonFlag:

                    wonFlag = True

                    for i in range(0, constants.COL_LENGTH):
                        if (self.gameState
                                [constants.COL_LENGTH - i - 1]
                                [i] != character):

                            wonFlag = False
                            break

        return wonFlag

    def isGameDraw(self):

        """ This function checks if the game is a draw """

        for i in range(0, constants.ROW_LENGTH):
            for j in range(0, constants.COL_LENGTH):
                if self.gameState[i][j] == "":
                    return False
        return True

    def deleteGame(self, app):
        # Remove Game
        if self.gameIndex in app.games:
            del app.games[self.gameIndex]

        if self.player1.socket in app.gameLookup:
            del app.gameLookup[self.player1.socket]

        if self.player2.socket in app.gameLookup:
            del app.gameLookup[self.player2.socket]

    def whichPlayer(self, socket):
        # Find which player made the move
        currentPlayer = None
        otherPlayer = None

        if self.player1.socket == socket:
            currentPlayer = self.player1
            otherPlayer = self.player2
        else:
            currentPlayer = self.player2
            otherPlayer = self.player1

        return (currentPlayer, otherPlayer)


class Application(tornado.web.Application):

    """ This is the main class which starts the
        tornado application """

    def __init__(self):

        handlers = [(r'/websocket', GameHandler)]
        debug = options.debug_mode

        # This holds the list of games
        self.games = {}
        self.gameIndex = 0

        # This holds the game lookup table
        self.gameLookup = {}

        # This contains the player which is waiting
        self.waitingPlayer = None

        tornado.web.Application.__init__(self, handlers, debug=debug)


class GameHandler(tornado.websocket.WebSocketHandler):

    """ This is the class which implements most of the
        multiplayer game logic """

    def open(self):
        pass

    def on_message(self, message):

        """ This function recieves a message of type
        {'command': 'name', {object}} and accordingly
        sends a message back to the client
        """

        try:
            msg = json.loads(message)

            if not "command" in msg:
                self.write_message(constants.ERROR_INVALID_MESSAGE)
            else:
                command = msg['command']
                if command == 'join':
                    """ Passed Message {command: 'join', playerName: name}
                        Return Message {'join'} """

                    self.join(msg)

                elif command == "move":
                    """ Passed Message {command: 'move', x, y} """

                    self.move(msg)

        except Exception, e:
            self.write_message(constants.ERROR_INVALID_MESSAGE)
            raise

    def join(self, message):
        """ This function checks if there is a player waiting
            for a game. If there is then it creates a game and
            sends a message to the two players to start the game """
        # Check if player is waiting
        if self.application.waitingPlayer is not None:

            # Create Game if player is waiting
            # Find starting player and assign cross or knots to player
            player1 = self.application.waitingPlayer
            player2 = Player(message['name'], self, "O")

            # Set the waiting player to none
            self.application.waitingPlayer = None

            # Add Lookup table
            newIndex = self.application.gameIndex
            self.application.gameLookup[player1.socket] = newIndex
            self.application.gameLookup[player2.socket] = newIndex

            # Create Game Object
            game = Game(player1, player2, newIndex)

            # Add Game to list of games
            self.application.games[newIndex] = game

            # Increment Game index
            self.application.gameIndex += 1

            game.startGame()

        else:
            # Make player wait if there is no other player waiting
            newPlayer = Player(message['name'], self, "X")
            self.application.waitingPlayer = newPlayer

    def move(self, message):
        """ This function handles the moves in the game """

        if self in self.application.gameLookup:
            gameIndex = self.application.gameLookup[self]
            self.application.games[gameIndex].makeMove(
                message['row'], message['column'], self)

    def on_close(self):
        """ This function handles the case when the socket is closed """

        # Do a reverse lookup and check which game did
        # the player disconnect from
        if self in self.application.gameLookup:
            gameIndex = self.application.gameLookup[self]
            currentGame = self.application.games[gameIndex]

            # Handle the quit event
            currentGame.playerQuit(self)


def main():

    """ This function starts the server """

    tornado.options.parse_command_line()

    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port, address='')
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
