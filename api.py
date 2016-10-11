# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""

import endpoints
from protorpc import remote, messages
from google.appengine.ext import ndb
from google.appengine.api import memcache
from google.appengine.api import taskqueue
import json

from models import User, Game, Score
from models import (
    StringMessage,
    NewGameForm,
    GameForm,
    MakeMoveForm,
    ScoreForms,
    UserGameFroms,
    UserRankingForms,
    GameHistroy
)
from utils import get_by_urlsafe
from utils import isBoardFull
from utils import isSpaceFree
from utils import isWinner


NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),user=messages.StringField(2),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
GET_USER_GAMES_REQUEST = endpoints.ResourceContainer(
        urlsafe_user_key=messages.StringField(1),)

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

@endpoints.api(name='tic_tac_toe', version='v1')
class TicTacToeApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user_x = User.get_user_by_name(request.user_x)
        user_o = User.get_user_by_name(request.user_o)
        if not (user_x and user_o):
            wrong_user = user_x if not user_x else user_o
            raise endpoints.NotFoundException(
                'User %s does not exist!' % wrong_user.name)

        board_size = 3
        try:
            game = Game.new_game(user_x.key,user_o.key,board_size)
        except ValueError:
            raise endpoints.BadRequestException('Something wrong, please check new game form')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        #taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Tic Tac Toe')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='cancel_game/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='GET')


    def cancel_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
                return game.to_form('Game already over!')
            else:
                game.game_cancel()
                return game.to_form('Game has been Cancelled!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='POST')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        #user = User.query(User.name == request.user).get()
        user = User.get_user_by_name(request.user)

        if game.game_over:
            return game.to_form('Game already over!')
        elif game.game_cancelled:
            return game.to_form('This Game is cancelled')

        if game.user_o == user.key:
            letter = 'O'
        else:
            letter = 'X'

        if user.key != game.next_move:
            raise endpoints.BadRequestException('It\'s not your turn!')

        if request.move > 8:
            raise endpoints.BadRequestException('It\'s out or range. Your move should be in 0 to 8')

        if isSpaceFree(game.board, request.move):
            game.board[request.move] = letter
            #game.moves.insert(request.move, letter)
            game.history.append((letter, request.move))
            game.next_move = game.user_x if (game.user_o == user.key) else game.user_o

            if isWinner(game.board, letter):
                game.end_game(user.key)
                return game.to_form('You won the Game')
            else:
                if isBoardFull(game.board):
                    game.end_game(False)
                    return game.to_form('Game Tie')
                else:
                    game.put()
                    return game.to_form('You have taken good position, let wait for the oponent')
        else:
            #return game.to_form('This is not a Free space to move')
            raise endpoints.BadRequestException('This is not a Free space to move')

    @endpoints.method(request_message=USER_REQUEST,
                  response_message=UserGameFroms,
                  path='user/games',
                  name='get_user_games',
                  http_method='GET')
    def get_user_games(self, request):
        """Return all User's active games"""
        user = User.get_user_by_name(request.user_name)
        games = Game.query(ndb.OR(Game.user_x == user.key,
                                  Game.user_o == user.key)). \
            filter(Game.game_over == False).filter(Game.game_cancelled == False)

        if not user:
            raise endpoints.BadRequestException('User not found!')

        return UserGameFroms(games = [game.to_form('Active User Games') for game in games])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameHistroy,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return a Game's move history"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if not game.winner:
            winner = ''
        else:
            winner = game.winner.get().name
        return GameHistroy(message=str(game.history),game_over= game.game_over,
                           game_cancelled= game.game_cancelled, tie = game.tie, winner=winner)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.get_user_by_name(request.user_name)
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(ndb.OR(Score.user_x == user.key,
                                    Score.user_o == user.key))
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=UserRankingForms,
                      path='scores/users',
                      name='get_user_rankings',
                      http_method='GET')

    def get_user_rankings(self, request):
        """Return all users with Rankings"""
        return UserRankingForms(users=[user.to_form() for user in User.query().order(-User.wins)])

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')


    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                        for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))


api = endpoints.api_server([TicTacToeApi])
