#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import TicTacToeApi

from models import User
from models import Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        games = Game.query(Game.game_over == False)
        for game in games:
            if not game.game_cancelled:
                user_one = User.query(User.key == game.user_o).get()
                user_two = User.query(User.key == game.user_x).get()
                subject = 'This is a reminder!'
                body = 'Hello {}, finish the game'
                # This will send test emails, the arguments to send_mail are:
                # from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                               (user_one.email, user_two.email),
                               subject,
                               body)

class SendReminderEmailForIncompleteGame(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        games = Game.query(Game.game_cancelled == True)

        for game in games:
            user_one = User.query(User.key == game.user_o).get()
            user_two = User.query(User.key == game.user_x).get()
            subject = 'This is a reminder!'
            body = 'Hello {}, try out Guess A Number!'
            # This will send test emails, the arguments to send_mail are:
            # from, to, subject, body
            mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           (user_one.email,user_two.email),
                           subject,
                           body)



class UpdateAverageMovesRemaining(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        TicTacToeApi._cache_average_attempts()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/crons/send_cancel_reminder', SendReminderEmailForIncompleteGame),
    ('/tasks/cache_average_attempts', UpdateAverageMovesRemaining),
], debug=True)
