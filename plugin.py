#!/usr/bin/env python3
# Copyright (c) 2017, Bruce Olivier
# All rights reserved.
#

import supybot.utils as utils
import supybot.commands as commands
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import sqlite3
from sqlite3 import Error
import os
import calendar
from datetime import datetime

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('EfnetQuotes')
except ImportError:
    """
    Placeholder that allows to run the plugin on a bot
    without the i18n module
    """
    def _(x): return x


class EfnetQuotes(callbacks.Plugin):
    """A list of channel quotes that you can add, remove or call randomly."""
    threaded = True

    def create_database(self, irc, db_file):
        conn = None

        try:
            print('Connecting to SQLite3 database...')
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            cursor.execute('''CREATE TABLE IF NOT EXISTS quotes (
                           id INTEGER PRIMARY KEY,
                           nick TEXT NOT NULL,
                           host TEXT NOT NULL,
                           quote TEXT NOT NULL,
                           channel TEXT NOT NULL,
                           timestamp INT DEFAULT NULL);''')
            conn.commit()
            cursor.close()
            print('Database created.')

        except Error as e:
            print(e)

        finally:
            if conn is not None:
                conn.close()
                print('Database connection closed.')

    def connect(self, irc):
        """create a database connection to a SQLite3 database"""
        full_path = os.path.dirname(os.path.abspath(__file__))
        db_file = '{0}/data/efnetquotes.db'.format(full_path)

        conn = None

        try:
            with open(db_file) as f:
                pass

            print('Connecting to the SQLite3 database...')
            conn = sqlite3.connect(db_file)

            return conn

        except IOError as e:
            irc.reply('No database found. Creating new database...')
            print(e)
            self.create_database(irc, db_file)

        except Error as e:
            print(e)

    def addquote(self, irc, msg, args, text):
        """<quote>
        Use this command to add a quote to the bot.
        """
        conn = None

        try:
            msg = str(msg).split(' ')
            host = msg[0][1:]
            nick = host.split('!')[0]
            channel = msg[2]
            now = datetime.utcnow()
            timestamp = calendar.timegm(now.utctimetuple())

            if not channel.startswith('#'):
                print('You must be in a channel to add a quote.')
                return

            sql = """INSERT INTO quotes (nick,host,quote,channel,timestamp)
                  VALUES(?,?,?,?,?)"""

            conn = self.connect(irc)
            cursor = conn.cursor()
            cursor.execute(sql, (nick, host, text, channel, timestamp,))
            conn.commit()
            cursor.close()
            print('Quote inserted into the database.')
            irc.reply('Quote added.')

        except Error as e:
            print(e)

        except AttributeError as e:
            irc.reply('Now try add the quote again!')
            print(e)

        finally:
            if conn is not None:
                conn.close()
                print('Closing database connection...')

    addquote = commands.wrap(addquote, ['text'])

    def quote(self, irc, msg, args, text):
        """- optional <argument>
        Use this command to randomly search for quotes.
        """
        conn = None
        try:
            msg = str(msg).split(' ')
            nick = msg[0][1:].split('!')[0]
            channel = msg[2]
            search = '%{0}%'.format(text)

            conn = self.connect(irc)
            cursor = conn.cursor()

            if not channel.startswith('#'):
                irc.reply('You must be in the channel to use this command')
                return

            if text is not None:
                sql = """SELECT id,nick,quote,channel FROM quotes WHERE channel=?
                      AND quote LIKE ? ORDER BY random() LIMIT 1;"""
                cursor.execute(sql, (channel, search,))
            else:
                sql = """SELECT id,nick,quote,channel FROM quotes WHERE channel=?
                      ORDER BY random() LIMIT 1;"""
                cursor.execute(sql, (channel,))

            quote = cursor.fetchone()

            if quote is not None:
                irc.reply('#{0}: {1}'.format(quote[0], quote[2]))
            else:
                irc.reply('No matches/quotes.')

            cursor.close()

        except Error as e:
            print(e)

        finally:
            if conn is not None:
                conn.close()
                print('Closing database connection...')

    quote = commands.wrap(quote, [commands.optional('text')])


Class = EfnetQuotes


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
