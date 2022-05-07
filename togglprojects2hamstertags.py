#!/usr/bin/env python3
import configparser
import os
import sqlite3
import time
from dataclasses import dataclass

import requests

TOGGL_PROJECTS_URL = 'https://api.track.toggl.com/api/v8/workspaces/{workspace_id}/projects'
TOGGL_CLIENTS_URL = 'https://api.track.toggl.com/api/v8/workspaces/{workspace_id}/clients'
CONFIG_FILE = 'hamster2toggl.config'

config_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    CONFIG_FILE
)
config_parser = configparser.RawConfigParser()
config_parser.read(config_path)
config = config_parser.defaults()

projects_url = TOGGL_PROJECTS_URL.format(
    workspace_id=config['toggl_workspace_id']
)
clients_url = TOGGL_CLIENTS_URL.format(
    workspace_id=config['toggl_workspace_id']
)
requests_auth = (config['toggl_key'], 'api_token')

response = requests.get(url=clients_url, auth=requests_auth)
response.raise_for_status()
client_id_to_name = {}
for client in response.json():
    client_id_to_name[client['id']] = client['name']

time.sleep(1.25)

url = TOGGL_PROJECTS_URL.format(workspace_id=config['toggl_workspace_id'])
response = requests.get(url=url, auth=requests_auth)
response.raise_for_status()
# special tag format: `tp::project name (client name)::project id`
project_tags_by_id = {}
for project in response.json():
    try:
        client_id = project['cid']
    except KeyError:
        client_name = None
    else:
        client_name= client_id_to_name[client_id]
    project_tag = 'tp::{project_name} ({client_name})::{project_id}'.format(
        project_name=project['name'],
        client_name=client_name,
        project_id=project['id'],
    )
    project_tags_by_id[project['id']] = project_tag

@dataclass
class HamsterTag:
    pk: int
    name: str

db_connection = sqlite3.connect(config['hamster_db'])
db_cursor = db_connection.cursor()
db_cursor.execute('select id, name from tags where name like "tp::%::%"')
toggl_project_id_to_hamster_tag = {}
for row in db_cursor:
    tag = HamsterTag(*row)
    toggl_project_id = int(tag.name.split('::')[-1])
    toggl_project_id_to_hamster_tag[toggl_project_id] = tag

no_change_count = 0
update_count = 0
insert_count = 0
for toggl_id, tag_name in project_tags_by_id.items():
    try:
        existing_hamster_tag = toggl_project_id_to_hamster_tag[toggl_id]
    except KeyError:
        existing_hamster_tag = None
    else:
        if existing_hamster_tag.name == tag_name:
            # no action needed
            no_change_count += 1
            continue

    if existing_hamster_tag:
        # update
        db_cursor.execute(
            'update tags set name = ? where id = ?',
            (tag_name, existing_hamster_tag.pk),
        )
        update_count += 1
    else:
        # insert
        db_cursor.execute(
            'insert into tags (name) values (?)',
            (tag_name,),
        )
        insert_count += 1

db_connection.commit()
print(
    f'{insert_count} tags added, {update_count} updated, '
    f'{no_change_count} unchanged'
)