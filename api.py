# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
import json

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, UserGameFroms, UserRankingForms
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
        user_one = User.query(User.name == request.user_one).get()
        user_two = User.query(User.name == request.user_two).get()
        moves = ['', '', '', '', '', '', '', '', '']
        if not user_one:
            raise endpoints.NotFoundException(
                    'A User One with that name does not exist!')
        elif not user_two:
            raise endpoints.NotFoundException(
                'A User Two with that name does not exist!')
        try:
            game = Game.new_game(moves, user_one.key,user_two.key,len(moves))
        except ValueError:
            raise endpoints.BadRequestException('Something wrong, please check new game form')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
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
                return game.to_form('Game Cancelled!')
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
        user = User.query(User.name == request.user).get()

        if game.game_over:
            return game.to_form('Game already over!')
        elif game.game_cancelled:
            return game.to_form('This Game is cancelled')

        if game.user_one == user.key:
            le = 'O'
        else:
            le = 'X'
        game.attempts_remaining -= 1

        if isSpaceFree(game.moves, request.move):
            game.moves.insert(request.move, le)

            if isWinner(game.moves, le):
                game.end_game(user.key, True)
                return game.to_form('You won the Game')
            else:
                if isBoardFull(game.moves):
                    game.end_game(True)
                    return game.to_form('Game Tie')
                else:
                    game.put()
                    return game.to_form('You have taken good position, let wait for the oponent')
        else:
            return game.to_form('This is not a Free space to move')

    @endpoints.method(request_message=GET_USER_GAMES_REQUEST,
                  response_message=UserGameFroms,
                  path='user/game/{urlsafe_user_key}',
                  name='get_user_games',
                  http_method='GET')
    def get_user_games(self, request):
        """Return the current game state."""
        user = get_by_urlsafe(request.urlsafe_user_key, User)
        games = Game.query(Game.user_one == user.key or Game.user_two == user.key)

        if games:
            return UserGameFroms(games = [game.to_form(' ') for game in games])
        else:
            raise endpoints.NotFoundException('User not found!')

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
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=UserRankingForms,
                      path='scores/users',
                      name='get_user_rankings',
                      http_method='GET')

    def get_user_rankings(self, request):
        """Return all users with Rankings"""
        return UserRankingForms(users=[user.to_form() for user in User.query().order(-User.ranking)])

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
