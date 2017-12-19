#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Bruce Olivier
# All rights reserved.


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
    full_path = os.path.dirname(os.path.abspath(__file__))
    db_file = '{0}/data/efnetquotes.db'.format(full_path)

    def create_database(self, irc, table):
        conn = None

        try:
            print('Connecting to SQLite3 database...')
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            sql = """CREATE TABLE IF NOT EXISTS {0} (
                        id INTEGER PRIMARY KEY,
                        nick TEXT NOT NULL,
                        host TEXT NOT NULL,
                        quote TEXT NOT NULL,
                        channel TEXT NOT NULL,
                        timestamp INT DEFAULT NULL);""".format(table)

            cursor.execute(sql)
            conn.commit()
            cursor.close()
            print('Database created.')

        except Error as e:
            print(e)

        finally:
            if conn is not None:
                conn.close()
                print('Database connection closed.')

    def connect(self, irc, table):
        """create a database connection to a SQLite3 database"""
        conn = None

        try:
            """
            Doing a check to see if there is a file or not.
            If not, create a database.
            """
            with open(self.db_file) as f:
                pass

            print('Connecting to the SQLite3 database...')
            conn = sqlite3.connect(self.db_file)

            return conn

        except IOError as e:
            irc.reply('No database found. Creating new database...')
            print(e)
            self.create_database(irc, table)

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
            table = '{0}quotes'.format(channel[1:])

            """
            Making sure the command is called in a channel and not private chat
            """
            if not channel.startswith('#'):
                print('You must be in a channel to add a quote.')
                return

            sql = """INSERT INTO {0} (nick,host,quote,channel,timestamp)
                        VALUES(?,?,?,?,?)""".format(table)

            conn = self.connect(irc, table)
            cursor = conn.cursor()
            cursor.execute(sql, (nick, host, text, channel, timestamp,))
            conn.commit()
            cursor.close()
            print('Quote inserted into the database.')
            irc.reply('Quote added.')

        except Error as e:
            print(e)

            if str(e).startswith('no such table'):
                self.create_database(irc, table)
                irc.reply('Creating new database table...try again.')

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
            table = '{0}quotes'.format(channel[1:])

            conn = self.connect(irc, table)
            cursor = conn.cursor()

            """
            Checking to see if there is an argument or no argument sent with
            the command. If argument, is the user searching for a quote # or
            quote text. Making sure the command is called in a channel and not
            private chat.
            """
            if not channel.startswith('#'):
                irc.reply('You must be in the channel to use this command')
                return

            elif text is not None:

                if text.isdigit():
                    sql = """SELECT id,quote FROM {0} WHERE
                                channel=? AND id=?""".format(table)

                    cursor.execute(sql, (channel, text,))

                else:
                    sql = """SELECT id,quote FROM {0} WHERE channel=?
                                AND (id LIKE ? OR quote LIKE ?) ORDER BY random()
                                LIMIT 1;""".format(table)

                    cursor.execute(sql, (channel, text, search,))

            else:
                sql = """SELECT id,quote FROM {0} WHERE channel=?
                            ORDER BY random() LIMIT 1;""".format(table)

                cursor.execute(sql, (channel,))

            quote = cursor.fetchone()

            """
            Checking to see if one of the select statements returned
            back a query or no matches.
            """
            if quote is not None:
                irc.reply('#{0}: {1}'.format(quote[0], quote[1]))
            else:
                irc.reply('No matches/quotes.')

            cursor.close()

        except Error as e:
            print(e)

            if str(e).startswith('no such table'):
                irc.reply('No match/quotes.')

        except AttributeError as e:
            irc.reply('Now use the .addquote command to add a new quote.')
            print(e)

        finally:
            if conn is not None:
                conn.close()
                print('Closing database connection...')

    quote = commands.wrap(quote, [commands.optional('text')])

    def delquote(self, irc, msg, args, text):
        """<quote number>
        Use this command with to delete a quote with the given quote number.
        """
        conn = None

        try:
            msg = str(msg).split(' ')
            host = msg[0][1:]
            nick = host.split('!')[0]
            channel = msg[2]
            search = '%{0}%'.format(text)
            table = '{0}quotes'.format(channel[1:])

            """
            Making sure the command is called in a channel and not private chat
            """
            if not channel.startswith('#'):
                irc.reply('You must be in the channel to use this command')
                return

            conn = self.connect(irc, table)
            cursor = conn.cursor()

            user = """SELECT nick,host FROM {0} WHERE id=?;""".format(table)

            cursor.execute(user, (text,))
            author = cursor.fetchone()

            """
            Checking to see if select statement returned the author
            of the quote
            """
            if author is not None:
                auth_host = author[1].split('!')[1]

            else:
                cursor.close()
                irc.reply('No match/quotes')
                return

            """
            Checks to see if a user is the author of the quote.
            If so, then delete the quote.
            """
            if nick == author[0] or host.endswith(auth_host):
                sql = """DELETE FROM {0} WHERE id=?;""".format(table)

                cursor.execute(sql, (text,))
                quote = cursor.fetchone()
                conn.commit()
                cursor.close()
                irc.reply('Quote #{0} deleted.'.format(text))

            else:
                irc.reply('You must be the author to delete.')
                cursor.close()

        except Error as e:
            print(e)

        finally:
            if conn is not None:
                conn.close()
                print('Closing database connection...')

    delquote = commands.wrap(delquote, ['text'])


Class = EfnetQuotes


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
