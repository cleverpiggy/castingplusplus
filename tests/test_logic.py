from datetime import timedelta
from itertools import chain
import pytest
from flaskr import create_app
from flaskr.models import Movie, Actor, Role
from helpers import TEST_DB_URL


@pytest.fixture(scope='module')
def client():
    app = create_app({
        'TESTING': True,
        'DATABASE_URL':TEST_DB_URL,
        'TESTING_WITHOUT_AUTH': True
    })
    with app.app_context():
        return app.test_client()


# select * from actor;
#  id |  name  | age | gender
# ----+--------+-----+--------
#   9 | Tom    |  35 | male
#  10 | Sally  |  25 | female
#  11 | Jones  |  19 | male
#  12 | Greg   |  56 | male
#  13 | Bridge |  22 | female
#  14 | Selena |  28 | female
#  15 | Marge  |  61 | female
#  16 | Pat    |  35 | non

# select * from movie;
#  id |    title    |    release_date
# ----+-------------+---------------------
#   4 | The End     | 2021-03-28 00:00:00
#   5 | Best Wishes | 2020-12-12 00:00:00
#   6 | This Sucks  | 2020-09-20 00:00:00

# select * from role;
#  id |     name     | age | gender | filled | movie_id
# ----+--------------+-----+--------+--------+----------
#   1 | The Butler   |  55 | male   | f      |        4
#   2 | The Waitress |  25 | female | f      |        4
#   3 | The Villan   |  45 | male   | f      |        4
#   4 | Hamlet       |  28 | male   | f      |        5
#   5 | Ophelia      |  25 | female | f      |        5
#   6 | Superman     |  30 | male   | f      |        6
#   7 | Lex Luthar   |  40 | male   | f      |        6
#   8 | Lois Lane    |  30 | female | f      |        6

# select * from booking;
#  id | role_id | actor_id
# ----+---------+----------
# (0 rows)


# Endpoints:
# GET /actors
# GET /movies
# GET /roles
# GET /movie/<id>
# POST /roles/<id>
# POST /actor
# POST /movie
# POST /actor/<id>/role/<id>
# DELETE /actor/<id>
# DELETE /movie/<id>
# DELETE /role/<id>
# PATCH /actor/<id>
# PATCH /movie/<id>
# PATCH /role/<id>


# Test the GETs first before messing with the data

def test_get_actor(client):
    url = '/actors'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json['actors'])

    # test paginations
    query_string = {'page_length': 3}
    response = client.get(url, query_string=query_string)
    page1 = response.json['actors']
    assert len(page1) == 3

    query_string = {'page_length': 3, 'page': 2}
    response = client.get(url, query_string=query_string)
    page2 = response.json['actors']
    assert len(page2) == 3
    assert set(a['id'] for a in page1) != set(a['id'] for a in page2)

    query_string = {'page_length': 3, 'page': 20}
    response = client.get(url, query_string=query_string)
    assert response.status_code == 404

    # test filter params



def test_get_movies(client):
    url = '/movies'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json['movies'])


def test_get_movie(client):
    movie_id = Movie.query.first().id
    url = f'/movie/{movie_id}'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json['roles'])
    assert all(r['movie_id'] == movie_id for r in response.json['roles'])


def test_get_roles(client):
    # Filter args:
    # 'gender': {'male', 'female', 'non'}
    # 'age': {range <lower-upper>}
    # 'filled': {true, false}
    # 'start_date': date
    # 'end_date': date

    # The filter combinations tested are:
    # - None
    # - gender
    # - age
    # - gender, filled
    # - start_date
    # - start_date, end_date

    # The method will be to do a filter on all_roles and compare
    # it to the server's return value after the same filters.
    all_roles = Role.query.all()
    # id_set makes the code a little cleaner
    def id_set(response):
        return {r['id'] for r in response.json['roles']}

    url = '/roles'
    #make sure we get all the roles even if i mess with the test db
    page_length = {'page_length':100}

    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json['roles']) == len(all_roles)


    query_string = {'gender': 'male', **page_length}
    response = client.get(url, query_string=query_string)
    assert response.status_code == 200
    assert id_set(response) == \
        {r.id for r in all_roles if r.gender == 'male'}

    query_string = {'age': '20-30', **page_length}
    response = client.get(url, query_string=query_string)
    assert response.status_code == 200
    assert id_set(response) == \
        {r.id for r in all_roles if r.age >= 20 and r.age <= 30}

    query_string = {'gender': 'female', 'filled': False, **page_length}
    response = client.get(url, query_string=query_string)
    assert response.status_code == 200
    assert id_set(response) == \
        {r.id for r in all_roles if r.gender == 'female' and r.filled == False}

    # Now to filter by release date
    movies = Movie.query.order_by(Movie.release_date).all()
    # grab the roles relations right away because lazy loading will kill them
    roles = [[r.format() for r in m.roles] for m in movies]

    start_date = movies[0].release_date + timedelta(days=+1)
    end_date = movies[-1].release_date + timedelta(days=-1)

    # Here we are looking for roles in all movies but the earliest.
    query_string = {'start_date': start_date, **page_length}
    response = client.get(url, query_string=query_string)
    assert response.status_code == 200
    assert id_set(response) == \
        {r['id'] for r in chain.from_iterable(roles[1:])}

    # Here we will include end_date and find all movies
    # betweet the first and the last.
    query_string = {'start_date': start_date, 'end_date': end_date, **page_length}
    response = client.get(url, query_string=query_string)
    assert id_set(response) == \
        {r['id'] for r in chain.from_iterable(roles[1:-1])}


def test_post_actor(client):
    url = '/actor'
    json = {'name':'Boris', 'age': 30, 'gender': 'male'}
    response = client.post(url, json=json)
    assert response.status_code == 200
    new_actor = Actor.query.filter_by(name='Boris', age=30).one_or_none()
    assert new_actor


def test_post_movie(client):
    url = '/movie'
    json = {'title':'Fantasmigoric', 'release_date': 'Aug 30 2021'}
    response = client.post(url, json=json)
    assert response.status_code == 200
    new_movie = Movie.query.filter_by(title='Fantasmigoric').one_or_none()
    assert new_movie


def test_delete_actor(client):
    actor_id = Actor.query.first().id
    url = f'/actor/{actor_id}'
    response = client.delete(url)
    assert response.status_code == 200
    actor = Actor.query.get(actor_id)
    assert actor is None


def test_delete_movie(client):
    movie_id = Movie.query.first().id
    url = f'/movie/{movie_id}'
    response = client.delete(url)
    assert response.status_code == 200
    movie = Movie.query.get(movie_id)
    assert movie is None


def test_patch_actor(client):
    # using .format so the attributes persist after session
    actor = Actor.query.filter(Actor.gender != 'non').first().format()
    url = f'/actor/{actor["id"]}'
    surgeon = {'male': 'female', 'female': 'male'}
    new_gender = surgeon[actor['gender']]
    json = {'gender': new_gender}
    response = client.patch(url, json=json)
    assert response.status_code == 200
    respawned = Actor.query.get(actor['id'])
    # check that just the patched attribute has changed
    assert respawned.gender == new_gender
    assert respawned.name == actor['name']


def test_patch_movie(client):
    # using .format so the attributes persist after session
    movie = Movie.query.first().format()
    url = f'/movie/{movie["id"]}'
    new_title = movie['title'] + ' Part 2!!!'
    json = {'title': new_title}
    response = client.patch(url, json=json)
    assert response.status_code == 200
    respawned = Movie.query.get(movie['id'])
    # check that just the patched attribute has changed
    assert respawned.title.endswith('!!!')
    assert respawned.release_date == movie['release_date']


def test_book_actor(client):
    actor_id = Actor.query.first().id
    role_id = Role.query.first().id
    url = f'/actor/{actor_id}/role/{role_id}'
    response = client.post(url)
    assert response.status_code == 200
    role = Role.query.get(role_id)
    assert role.filled
    actor = Actor.query.get(actor_id)
    assert actor.bookings


def test_post_roles(client):
    movie = Movie.query.first()
    movie_id = movie.id
    nroles = len(movie.roles) # this magically gives you a list of roles
    url = f'/roles/{movie_id}'
    json = [
        {
            'name': 'Bystander A',
            'age': 30,
            'gender': 'male'
        },
        {
            'name': 'Bystander B',
            'age': 50,
            'gender': 'female'
        }
    ]
    response = client.post(url, json=json)
    assert response.status_code == 200
    movie = Movie.query.get(movie_id)
    assert len(movie.roles) == nroles + 2
