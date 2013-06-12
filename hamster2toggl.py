#!usr/bin/env python
# -*- encoding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker
# GPL {{{1
#############################################################################
# Copyright 2013 Ivan F. Villanueva B. <ivan ät wikical.com>,
#
# hamster2toggl is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# hamster2toggl is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with hamster2toggl. If not, see <http://www.gnu.org/licenses/>.
#############################################################################
# Inspired by https://github.com/shaftoe/redminetimesync

# imports {{{1
import datetime
import sqlite3
import datetime
import os
import sys
import ConfigParser

def getDate():
    date = datetime.date.today()
    if len(sys.argv) == 2:
        date = date - datetime.timedelta( int(sys.argv[1]) )
    return date.isoformat()

def fetch_config(configFileName='hamster2toggl.config'):
    configPath = os.path.join(os.path.split(os.path.abspath(sys.argv[0]))[0],configFileName)
    config_parser = ConfigParser.RawConfigParser()
    config_parser.read(configPath)
    config = config_parser.defaults()
    return config

def fetch_db(dataFile, date, category):
    # http://docs.python.org/library/sqlite3.html
    date = "%"+getDate()+"%"
    connection = sqlite3.connect(dataFile)
    dbCursor = connection.cursor()
    if category:
        dbCursor.execute("""SELECT
            activities.name,facts.start_time,facts.end_time,facts.description,categories.name
            FROM activities
            JOIN facts ON activities.id = facts.activity_id
            JOIN categories ON activities.category_id = categories.id
            WHERE facts.start_time LIKE ?
            AND facts.end_time LIKE ?
            AND categories.name LIKE ?""", (date, date, category))
    else:
        dbCursor.execute("""SELECT
            activities.name,facts.start_time,facts.end_time,facts.description
            FROM activities
            JOIN facts ON activities.id = facts.activity_id
            WHERE facts.start_time LIKE ?
            AND facts.end_time LIKE ?""", (date, date))
    return dbCursor

def trans(date_string):
    """ 2013-01-01 15:00:00 -> datetime """
    return datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    config = fetch_config()
    # https://github.com/toggl/toggl_api_docs/blob/master/chapters/time_entries.md
    curl = 'curl -v -u %s:api_token ' \
        '-H "Content-type: application/json" ' \
        '-d \'{"time_entry":{"description":"%s","start":"%s","duration":%s,"pid":%s}}\' ' \
        '-X POST https://www.toggl.com/api/v8/time_entries'
    db = fetch_db(
            config['db'],
            getDate(),
            config.get('category', '').strip())
    for entry in db:
        # each entry is e.g.:
        # (u'test1', u'2013-06-04 15:01:14', u'2013-06-04 15:30:49', None, None)
        start = trans(entry[1])
        end = trans(entry[2])
        concrete_curl = curl % (
            config['key'],
            entry[0],
            (start + datetime.timedelta(hours = int(config['timezone']))).isoformat() + 'Z',
            (end-start).seconds,
            config['pid'])
        print concrete_curl
        os.system(concrete_curl)
