"""utils.py - File for collecting general utility functions."""

import logging
from google.appengine.ext import ndb
import endpoints

def get_by_urlsafe(urlsafe, model):
    """Returns an ndb.Model entity that the urlsafe key points to. Checks
        that the type of entity returned is of the correct kind. Raises an
        error if the key String is malformed or the entity is of the incorrect
        kind
    Args:
        urlsafe: A urlsafe key string
        model: The expected entity kind
    Returns:
        The entity that the urlsafe Key string points to or None if no entity
        exists.
    Raises:
        ValueError:"""
    try:
        key = ndb.Key(urlsafe=urlsafe)
    except TypeError:
        raise endpoints.BadRequestException('Invalid Key')
    except Exception, e:
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
            raise endpoints.BadRequestException('Invalid Key')
        else:
            raise

    entity = key.get()
    if not entity:
        return None
    if not isinstance(entity, model):
        raise ValueError('Incorrect Kind')
    return entity

def isBoardFull(board):
     # Return True if every space on the board has been taken. Otherwise return False.
     for i in range(1, 10):
         if isSpaceFree(board, i):
             return False
     return True


def isSpaceFree(board, move):
      # Return true if the passed move is free on the passed board.
    return board[move] == ''

def isWinner(bo, le):
    #Given a board and a players letter, this function returns True if that player has won
      return ((bo[6] == le and bo[7] == le and bo[8] == le) or # across the top
      (bo[3] == le and bo[4] == le and bo[5] == le) or # across the middle
      (bo[0] == le and bo[1] == le and bo[2] == le) or # across the bottom
      (bo[6] == le and bo[3] == le and bo[0] == le) or # down the left side
      (bo[7] == le and bo[4] == le and bo[1] == le) or # down the middle
      (bo[8] == le and bo[5] == le and bo[2] == le) or # down the right side
      (bo[6] == le and bo[4] == le and bo[2] == le) or # diagonal
      (bo[8] == le and bo[4] == le and bo[0] == le)) # diagonal