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
    wins = ndb.IntegerProperty(default=0)
    ties = ndb.IntegerProperty(default=0)
    total_played = ndb.IntegerProperty(default=0)

    @property
    def totlal_points(self):
        """User points"""
        return self.wins * 2 + self.ties

    @property
    def win_percentage(self):
        """User win percentage"""
        if self.total_played > 0:
            return float(self.wins) / float(self.total_played)
        else:
            return 0
    @property
    def no_lose_percentage(self):
        """User win plus tie percentage"""
        if self.total_played > 0:
            return (float(self.wins) + float(self.ties)) / float(
                self.total_played)
        else:
            return float(0)

    def to_form(self):
        return UserRankingForm(name=self.name,
                        email=self.email,
                        wins=self.wins,
                        ties=self.ties,
                        total_played=self.total_played,
                        no_lose_percentage=self.no_lose_percentage,
                        points=self.totlal_points)

    @classmethod
    def get_user_by_name(cls, username):
        """Gets User by his name. Return None on no User found"""
        return User.query(User.name == username).get()

    def update_stats(self):
        """Adds game to user and update."""
        self.total_played += 1
        self.put()

    def add_win(self):
        """Add a win"""
        self.wins += 1
        self.update_stats()

    def add_tie(self):
        """Add a tie"""
        self.ties += 1
        self.update_stats()

    def add_loss(self):
        """Add a loss. Used as additional method for extensibility."""
        self.update_stats()


class Game(ndb.Model):
    """Game object"""
    board = ndb.PickleProperty(required=True)
    board_size = ndb.IntegerProperty(required=True, default=3)
    next_move = ndb.KeyProperty(required=True)  # The User whose turn it is
    user_x = ndb.KeyProperty(required=True, kind='User')
    user_o = ndb.KeyProperty(required=True, kind='User')
    game_over = ndb.BooleanProperty(required=True, default=False)
    game_cancelled = ndb.BooleanProperty(required=True, default=False)
    winner = ndb.KeyProperty()
    tie = ndb.BooleanProperty(default=False)
    history = ndb.PickleProperty(required=True)

    @classmethod
    def new_game(cls, user_x, user_o, board_size=3):
        """Creates and returns a new game"""
        game = Game(user_x=user_x,
                    user_o=user_o,
                    next_move=user_x)
        game.board = ['' for _ in range(board_size*board_size)]
        game.history = []
        game.board_size = board_size
        game.put()
        return game

    def to_form(self,message):
        """Returns a GameForm representation of the Game"""
        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        board=str(self.board),
                        board_size=self.board_size,
                        user_x=self.user_x.get().name,
                        user_o=self.user_o.get().name,
                        next_move=self.next_move.get().name,
                        game_over=self.game_over,
                        game_cancelled=self.game_cancelled,
                        message = message
                        )
        if self.winner:
            form.winner = self.winner.get().name
        if self.tie:
            form.tie = self.tie
        return form

    def end_game(self, winner=None):
        """Ends the game"""
        self.game_over = True
        if winner:
            self.winner = winner
        else:
            self.tie = True
        self.put()
        if winner:
            result = 'user_x' if winner == self.user_x else 'user_o'
        else:
            result = 'tie'
        # Add the game to the score 'board'
        score = Score(date=date.today(), user_x=self.user_x,
                      user_o=self.user_o, result=result)
        score.put()

        # Update the user models
        if winner:
            winner.get().add_win()
            loser = self.user_x if winner == self.user_o else self.user_o
            loser.get().add_loss()
        else:
            self.user_x.get().add_tie()
            self.user_o.get().add_tie()

    def game_cancel(self):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_cancelled = True
        self.put()


class Score(ndb.Model):
    """Score object"""
    user_x = ndb.KeyProperty(required=True, kind='User')
    user_o = ndb.KeyProperty(required=True, kind='User')
    result = ndb.StringProperty(required=True)
    date = ndb.DateProperty(required=True)

    def to_form(self):
        return ScoreForm(date=str(self.date),
                         user_x=self.user_x.get().name,
                         user_o=self.user_o.get().name,
                         result=self.result)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    board = messages.StringField(2, required=True)
    board_size = messages.IntegerField(3, required=True)
    user_x = messages.StringField(4, required=True)
    user_o = messages.StringField(5, required=True)
    next_move = messages.StringField(6, required=True)
    game_over = messages.BooleanField(7, required=True)
    winner = messages.StringField(8)
    tie = messages.BooleanField(9)
    game_cancelled = messages.BooleanField(10, required=True)
    message = messages.StringField(11, required=True)

class  UserGameFroms(messages.Message):
    """Return multiple ScoreForms"""
    games = messages.MessageField(GameForm, 1, repeated=True)

class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_x = messages.StringField(1, required=True)
    user_o = messages.StringField(2, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    move = messages.IntegerField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_x= messages.StringField(1, required=True)
    user_o = messages.StringField(2, required=True)
    date = messages.StringField(3, required=True)
    result = messages.StringField(4)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class UserRankingForm(messages.Message):
    """ScoreForm for outbound Score information"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    wins = messages.IntegerField(3, required=True)
    ties = messages.IntegerField(4, required=True)
    total_played = messages.IntegerField(5, required=True)
    no_lose_percentage = messages.FloatField(6, required=True)
    points = messages.IntegerField(7)

class UserRankingForms(messages.Message):
    """Return multiple ScoreForms"""
    users = messages.MessageField(UserRankingForm, 1, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
