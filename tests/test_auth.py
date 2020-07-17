import pytest
from flaskr import create_app
from helpers import TEST_DB_URL
import jwts


@pytest.fixture(scope='module')
def client():
    app = create_app({
        'TESTING': True,
        'DATABASE_URL':TEST_DB_URL
    })
    with app.app_context():
        return app.test_client()


HEADERS = {
    'assistant': f'Authorization: Bearer {jwts.ASSISTANT}',
    'director': f'Authorization: Bearer {jwts.DIRECTOR}',
    'producer': f'Authorization: Bearer {jwts.PRODUCER}',
    'expired': f'Authorization: Bearer {jwts.EXPIRED}',
    'irrelevant': 'Authorization: I want in!!!'
}


def header(authlevel):
    return [HEADERS[authlevel].split(':')]


def check(auth_level, request_func, url):
    # auth_level -> the minimum auth level

    # Ordered with highest clearance level on the right allows
    # using pop until we get to auth_level.
    # The rest of the list will then be unauthorized.
    auths = ['expired', 'irrelevant', 'assistant', 'director', 'producer']
    authorized = None
    while authorized != auth_level:
        authorized = auths.pop()
        response = request_func(url, headers=header(authorized))
        # We won't always get 200 but as long as it's not 401 we are authorized
        assert response.status_code != 401
    for unauthorized in auths:
        response = request_func(url, headers=header(unauthorized))
        assert response.status_code == 401

    response = request_func(url)
    assert response.status_code == 401


# producer director assistant
def test_get_actor(client):
    url = '/actors'
    check('assistant', client.get, url)

# producer director assistant
def test_get_movies(client):
    url = '/movies'
    check('assistant', client.get, url)

# producer director assistant
def test_get_movie_roles(client):
    url = '/movie1/roles'
    check('assistant', client.get, url)

# producer director assistant
def test_get_roles(client):
    url = '/roles'
    check('assistant', client.get, url)

# producer director
def test_post_actor(client):
    url = '/actor'
    check('director', client.post, url)

# producer
def test_post_movie(client):
    url = '/movie'
    check('producer', client.post, url)

# producer director
def test_delete_actor(client):
    url = '/actor1'
    check('director', client.delete, url)

# producer
def test_delete_movie(client):
    url = '/movie1'
    check('producer', client.delete, url)

# producer director
def test_patch_actor(client):
    url = '/actor1'
    check('director', client.patch, url)

# producer director
def test_patch_movie(client):
    url = '/movie1'
    check('director', client.patch, url)

# producer director
def test_book_actor_role(client):
    url = f'/book/actor1/role1'
    check('director', client.post, url)

# producer director
def test_post_movie_roles(client):
    url = '/movie1/roles'
    check('director', client.post, url)
