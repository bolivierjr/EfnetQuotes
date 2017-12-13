#!/usr/bin/env python3
# Copyright (c) 2017, Bruce Olivier
# All rights reserved.
#

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import sqlite3
from sqlite3 import Error
import os
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('EfnetQuotes')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    def _(x): return x


class EfnetQuotes(callbacks.Plugin):
    """A list of channel quotes that you can add, remove or call randomly."""
    threaded = True
    db_file = '{0}/data/efnetquotes.db'.format(os.getcwd())

    def create_database(self, irc, db_file):
        conn = None

        try:
            print('Connecting to SQLite3 database...')
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            cursor.execute('''CREATE TABLE IF NOT EXISTS quotes (
                           id INTEGER PRIMARY KEY,
                           nick TEXT NOT NULL,
                           quote TEXT NOT NULL,
                           channel TEXT NOT NULL,
                           timestamp INT DEFAULT NULL);''')

            cursor.close()

        except Error as e:
            print(e)

        finally:
            if conn is not None:
                conn.close()
                print('Database connection closed.')

    def connect(self, irc):
        """create a database connection to a SQLite3 database"""

        db_file = EfnetQuotes.db_file
        conn = None

        try:
            with open(db_file) as f:
                pass

            print('Connecting to the SQLite3 database...')
            conn = sqlite3.connect(db_file)

            return conn

        except IOError as e:
            irc.reply('No database found. Creating new database...')
            self.create_database(irc, db_file)

        except Error as e:
            print(e)

        finally:
            if conn is not None:
                conn.close()
                print('Database connection closed.')


Class = EfnetQuotes


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
