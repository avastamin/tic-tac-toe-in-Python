"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()
    ranking = ndb.IntegerProperty(required=True, default=0)

    def to_form(self):
       return UserRankingForm(user_name=self.name, ranking=self.ranking)



class Game(ndb.Model):
    """Game object"""
    #user_one_moves = ndb.IntegerProperty(repeated=True)
    #user_two_moves = ndb.IntegerProperty(repeated=True)
    moves = ndb.StringProperty(repeated= True)
    attempts_allowed = ndb.IntegerProperty(required=True,default=9)
    attempts_remaining = ndb.IntegerProperty(required=True, default=9)
    game_over = ndb.BooleanProperty(required=True, default=False)
    game_cancelled = ndb.BooleanProperty(required=True, default=False)
    user_one = ndb.KeyProperty(required=True, kind='User')
    user_two = ndb.KeyProperty(required=True, kind='User')

    @classmethod
    def new_game(cls,moves, user_one,user_two, attempts):
        """Creates and returns a new game"""

        game = Game(user_one=user_one,
                    user_two = user_two,
                    moves= moves,
                    attempts_allowed=attempts,
                    attempts_remaining=attempts,
                    game_over=False,
                    game_cancelled=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        #form.moves = self.moves
        form.user_one = self.user_one.get().name
        form.user_two = self.user_two.get().name
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.game_cancelled = self.game_cancelled
        form.message = message
        return form

    def end_game(self, user, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()

        updateuser = User.query(User.key == user).get()
        updateuser.ranking = updateuser.ranking + 1
        updateuser.put()

        # Add the game to the score 'board'
        score = Score(user=user, date=date.today(), won=won)
        score.put()

    def game_cancel(self):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_cancelled = True
        self.put()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date))


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_one = messages.StringField(5, required=True)
    user_two = messages.StringField(6, required=True)
    moves = messages.StringField(7, repeated= True)
    game_cancelled = messages.BooleanField(8, required=True)

class UserGameForm(messages.Message):
    """GameForm for outbound game state information"""
    user_urlsafe_key = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)
    #games = messages.MessageField(GameForm, 3, repeated=True)

class  UserGameFroms(messages.Message):
    """Return multiple ScoreForms"""
    games = messages.MessageField(GameForm, 1, repeated=True)

class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_one = messages.StringField(1, required=True)
    user_two = messages.StringField(2, required=True)
    #attempts = messages.IntegerField(5, default=9)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    move = messages.IntegerField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class UserRankingForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    ranking = messages.IntegerField(2, required=True)

class UserRankingForms(messages.Message):
    """Return multiple ScoreForms"""
    users = messages.MessageField(UserRankingForm, 1, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
