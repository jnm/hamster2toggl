#!/usr/bin/env python3
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

import configparser
import datetime
import os
import sqlite3
import sys
import time

import requests

TOGGL_URL = 'https://api.track.toggl.com/api/v8/time_entries'
CONFIG_FILE = 'hamster2toggl.config'

config_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    CONFIG_FILE
)
config_parser = configparser.RawConfigParser()
config_parser.read(config_path)
config = config_parser.defaults()

db_connection = sqlite3.connect(config['hamster_db'])

def get_query_date(offset=None):
    """ Returns date based on local time """
    date = datetime.date.today()
    if offset is not None:
        date += datetime.timedelta(days=offset)
    return date.isoformat()

def datetime_from_hamster(hamster_time):
    """ 2013-01-01 15:00:00 (local time) -> datetime (UTC) """
    assert len(hamster_time) == 19
    local_time = datetime.datetime.strptime(
        hamster_time, '%Y-%m-%d %H:%M:%S'
    ).astimezone()
    return local_time.astimezone(datetime.timezone.utc)

def datetime_to_js(datetime_obj):
    assert datetime_obj.tzinfo == datetime.timezone.utc
    return datetime_obj.isoformat()[:19] + 'Z'

def fetch_facts(date, category):
    # http://docs.python.org/library/sqlite3.html
    date = f'%{date}%'  # not great
    db_cursor = db_connection.cursor()
    if category:
        db_cursor.execute("""SELECT
            activities.name,facts.id,facts.start_time,facts.end_time,facts.description,categories.name
            FROM activities
            JOIN facts ON activities.id = facts.activity_id
            JOIN categories ON activities.category_id = categories.id
            WHERE facts.start_time LIKE ?
            AND categories.name LIKE ?""", (date, category))
    else:
        db_cursor.execute("""SELECT
            activities.name,facts.id,facts.start_time,facts.end_time,facts.description
            FROM activities
            JOIN facts ON activities.id = facts.activity_id
            WHERE facts.start_time LIKE ?""", (date,))
    return db_cursor

def fetch_tags_for_fact(fact_id):
    db_cursor = db_connection.cursor()
    db_cursor.execute(
        'select name from tags where id in '
        '(select tag_id from fact_tags where fact_id = ?)',
        (fact_id,)
    )
    return list((row[0] for row in db_cursor))


days_offset = None
if len(sys.argv) == 2:
    days_offset = -1 * int(sys.argv[1])

query_date = get_query_date(days_offset)
print('Processing events from', query_date)

toggl_post_queue = []
facts = fetch_facts(query_date, config.get('hamster_category', '').strip())
for fact in facts:
    # each entry is e.g.:
    # ('test1', 123, '2013-06-04 15:01:14', '2013-06-04 15:30:49', None, None)
    activity, fact_id, start_time, end_time, description = fact[:5]
    tags = fetch_tags_for_fact(fact_id)

    if not end_time:
        print('WARNING: No end time for', fact, tags)
        print('Press ENTER to continue and omit this entry or CTRL+C to abort')
        input()
        continue

    start_time = datetime_from_hamster(start_time)
    end_time = datetime_from_hamster(end_time)

    toggl_project_id = None
    for tag in tags.copy():
        # special tag format: `tp::project name::project id`
        if tag.startswith('tp::'):
            toggl_project_id = int(tag.split('::')[-1])
            tags.remove(tag)
            break
    if toggl_project_id is None:
        print('WARNING: No project ID found in', fact, tags)

    toggl_description = ', '.join(tags)
    if description:
        toggl_description += f': {description}'
    toggl_description += f' [{fact_id}]'

    # https://github.com/toggl/toggl_api_docs/blob/master/chapters/time_entries.md
    time_entry = {
        'created_with': 'jnm test 20220506',
        'description': toggl_description,
        'start': datetime_to_js(start_time),
        'duration': (end_time - start_time).seconds,
        'wid': config['toggl_workspace_id'],
        'pid': toggl_project_id,
    }
    toggl_data = {'time_entry': time_entry}
    toggl_post_queue.append(toggl_data)

if not toggl_post_queue:
    print('There are no events to upload. Bye!')
    exit()

print('Ready to upload? Press ENTER to continue or CTRL+C to abort')
#print('\n'.join((str(d) for d in toggl_post_queue)))
input()

requests_auth = (config['toggl_key'], 'api_token')
for toggl_data in toggl_post_queue:
    print('POST:', toggl_data)
    response = requests.post(url=TOGGL_URL, auth=requests_auth, json=toggl_data)
    if response.status_code == 200:
        print('\tOK!')
    else:
        print(f'\tFAILED ({response.status_code}): {response.text}')
    time.sleep(1.25)
