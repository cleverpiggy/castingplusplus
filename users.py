"""
Calling this module gets you the curl string to request the access tokens
for one of the three roles: assistant, director, producer.

Do it like this:

python users.py assistant | xargs curl

Rememeber I filled the previously blank 'default directory' field at Auth0
with Username-Password-Authentication to make this work.  And checked 'password'
under advanced setting -> grant types under applications -> castingplusplus.
"""

import sys
from os import environ
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


method = 'POST'
url = f'https://{AUTH0_DOMAIN}/oauth/token'

header = 'Content-Type: application/x-www-form-urlencoded'

def data(user):
    USERNAME, PASSWORD = {
        'assistant': ASSISTANT_INFO,
        'director': DIRECTOR_INFO,
        'producer': PRODUCER_INFO
    }[user]
    SCOPE = 'openid profile email'
    return f'grant_type=password&username={USERNAME}&password={PASSWORD}&audience={API_IDENTIFIER}&scope={SCOPE}&client_id={AUTH0_CLIENT_ID}&client_secret={AUTH0_CLIENT_SECRET}'

def main():
    user = sys.argv[1]
    print (f'-X {method} -H \'{header}\' -d \'{data(user)}\' \'{url}\'')
    return 1

if __name__ == '__main__':
    main()
