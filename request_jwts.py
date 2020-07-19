"""
Calling this module allows you to request the access tokens the three
roles: assistant, director, producer, and write to a python file assigning them
to variables

Do it like this:

python reqest_jwt.py tests/jwts.py

Rememeber I filled the previously blank 'default directory' field at Auth0
with Username-Password-Authentication to make this work.  And checked 'password'
under advanced setting -> grant types under applications -> castingplusplus.
"""

import sys
import json
from urllib.request import urlopen
from urllib.parse import urlencode
from os import environ
import os
from dotenv import load_dotenv, find_dotenv

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


AUTH0_CALLBACK_URL = environ.get('AUTH0_CALLBACK_URL')
AUTH0_CLIENT_ID = environ.get('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = environ.get('AUTH0_CLIENT_SECRET')
AUTH0_DOMAIN = environ.get('AUTH0_DOMAIN')
AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
AUTH0_AUDIENCE = environ.get('AUTH0_AUDIENCE')

API_IDENTIFIER = AUTH0_AUDIENCE

ASSISTANT_INFO = environ.get('ASSISTANT_INFO').split(',')
DIRECTOR_INFO = environ.get('DIRECTOR_INFO').split(',')
PRODUCER_INFO = environ.get('PRODUCER_INFO').split(',')


METHOD = 'POST'
BASE_URL = f'https://{AUTH0_DOMAIN}/oauth/token'

HEADER = 'Content-Type: application/x-www-form-urlencoded'


def make_data(user):
    username, password = {
    'assistant': ASSISTANT_INFO,
    'director': DIRECTOR_INFO,
    'producer': PRODUCER_INFO
    }[user]
    scope = 'openid profile email'
    data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'audience': API_IDENTIFIER,
        'scope': scope,
        'client_id': AUTH0_CLIENT_ID,
        'client_secret': AUTH0_CLIENT_SECRET
    }
    return data

def send_request(user, verbose=True):
    if verbose:
        print(f'doing {user}')
    data = make_data(user)
    encoded = urlencode(data).encode('ascii')
    with urlopen(BASE_URL, data=encoded) as f:
        return f.read().decode('utf-8')

def extract_jwt(response, verbose=True):
    d = json.loads(response)
    token = d["access_token"]
    expires = d["expires_in"]
    if verbose:
        print(f'expires in {expires / 60 / 60} hours')
    return token

def make_file_line(token, user):
    return f"{user.upper()}='{token}'\n"


def do_one(user):
    resp = send_request(user)
    token = extract_jwt(resp)
    line = make_file_line(token, user)
    return line

def write_file(users, file_name):
    """
    users -> list of users (probably all of them)
    file_name -> jwts file
    """
    expired = []
    # first save the expired jwt if its in there
    if os.path.exists(file_name):
        with open(file_name, 'r') as f:
            old_stuff = f.read()
            lines = old_stuff.split('\n')
            expired = [l for l in lines if l.startswith('EXPIRED')] + ['\n']

    with open(file_name, 'w') as f:
        for user in users:
            line = do_one(user)
            f.write(line)
        for line in expired:
            f.write(line)


def main():
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    elif os.path.exists('tests'):
        file_name = 'tests/jwts.py'
    else:
        print('usage:  python request_jwts.py <filname>')
        return 0

    write_file(['assistant', 'director', 'producer'], file_name)
    print(f'saving to {file_name}')
    return 1


if __name__ == '__main__':
    main()
