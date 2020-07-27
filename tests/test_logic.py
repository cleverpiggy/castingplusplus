import os
from datetime import timedelta
from itertools import chain
import pytest
from flaskr import create_app
from flaskr.models import Movie, Actor, Role
import populate_testdb


@pytest.fixture(scope='module')
def client():
    dburl = 'sqlite:///:memory:'
    app = create_app({
        'TESTING': True,
        'DATABASE_URL': dburl,
        'TESTING_WITHOUT_AUTH': True
    })
    populate_testdb.do_it(dburl, app)

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
# GET /actors ************************
# GET /movies ******************************
# GET /roles *********************
# GET /movie/<id> **************************
# POST /roles/<id> ***************************
# POST /actor ***************************
# POST /movie **********************
# POST /actor/<id>/role/<id> ******************
# DELETE /actor/<id> *************************
# DELETE /movie/<id> ***********************
# DELETE /role/<id> **************************
# PATCH /actor/<id> *************************
# PATCH /movie/<id> ***********************
# PATCH /role/<id> ****************************

BAD_ID = 999
BAD_PAGE = 999


# Test the GETs first before messing with the data

def test_get_movies(client):
    # success
    # -------------------------------------------------
    url = '/movies'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json['movies'])

    # fail with 404 page out of bounds
    # -------------------------------------------------
    query_string = {'page_length': 3, 'page': BAD_PAGE}
    response = client.get(url, query_string=query_string)
    assert response.status_code == 404


def test_get_movie(client):
    # success
    # -------------------------------------------------
    movie_id = Movie.query.first().id
    url = f'/movie/{movie_id}'
    response = client.get(url)
    assert response.status_code == 200
    roles = response.json['roles']
    assert len(roles) > 0
    assert all(r['movie_id'] == movie_id for r in roles)

    # fail with 404 movie id not in database
    # -------------------------------------------------
    url = f'/movie/{BAD_ID}'
    response = client.get(url)
    assert response.status_code == 404


def test_get_actors(client):
    #
    # success
    # -------------------------------------------------
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

    # fail with 404 page out of bounds
    # -------------------------------------------------
    query_string = {'page_length': 3, 'page': BAD_PAGE}
    response = client.get(url, query_string=query_string)
    assert response.status_code == 404


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

    # successes
    # -------------------------------------------------

    # make sure we get all the roles even if i mess with the test db
    page_length = {'page_length': 100}

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
        {r.id for r in all_roles if r.gender == 'female' and r.filled is False}

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
    query_string = {
        'start_date': start_date,
        'end_date': end_date,
        **page_length
    }
    response = client.get(url, query_string=query_string)
    assert id_set(response) == \
        {r['id'] for r in chain.from_iterable(roles[1:-1])}

    # fail with 422 malformed age range
    # -------------------------------------------------
    query_string = {'age': 'middle', **page_length}
    response = client.get(url, query_string=query_string)
    assert response.status_code == 422

    # fail with 422 date range out of order
    query_string = {
        'start_date': '12-12-2020',
        'end_date': '10-12-2020',
        **page_length
    }
    response = client.get(url, query_string=query_string)
    assert response.status_code == 422

    # fail with 422 malformed dates
    query_string = {'start_date': 'next month', **page_length}
    response = client.get(url, query_string=query_string)
    assert response.status_code == 422


def test_post_actor(client):
    # success
    # -------------------------------------------------
    url = '/actor'
    json = {'name': 'Boris', 'age': 30, 'gender': 'male'}
    response = client.post(url, json=json)
    assert response.status_code == 200
    new_actor = Actor.query.filter_by(name='Boris', age=30).one_or_none()
    assert new_actor

    # fail with 422 incorrect data types
    # ---------------------------------------------------
    json = {'name': 'Boris', 'age': 'N/A', 'gender': 'male'}  # age bad
    response = client.post(url, json=json)
    assert response.status_code == 422


def test_post_movie(client):
    # success
    # -------------------------------------------------
    url = '/movie'
    json = {'title': 'Fantasmigoric', 'release_date': 'Aug 30 2021'}
    response = client.post(url, json=json)
    assert response.status_code == 200
    new_movie = Movie.query.filter_by(title='Fantasmigoric').one_or_none()
    assert new_movie

    # fail with 422 all values required
    # ---------------------------------------------------
    json = {'title': 'Crazy Stuff'}
    response = client.post(url, json=json)
    assert response.status_code == 422


def test_delete_actor(client):
    # success
    # -------------------------------------------------
    actor_id = Actor.query.first().id
    url = f'/actor/{actor_id}'
    response = client.delete(url)
    assert response.status_code == 200
    actor = Actor.query.get(actor_id)
    assert actor is None

    # fail with 404 actor id not in database
    # -------------------------------------------------
    url = f'/actor/{BAD_ID}'
    response = client.delete(url)
    assert response.status_code == 404


def test_delete_movie(client):
    # success
    # -------------------------------------------------
    movie_id = Movie.query.first().id
    url = f'/movie/{movie_id}'
    response = client.delete(url)
    assert response.status_code == 200
    movie = Movie.query.get(movie_id)
    assert movie is None

    # fail with 404 movie id not in database
    # -------------------------------------------------
    url = f'/movie/{BAD_ID}'
    response = client.delete(url)
    assert response.status_code == 404


def test_patch_actor(client):
    # success
    # -------------------------------------------------
    # using .format so the attributes persist after session
    actor = Actor.query.filter(Actor.gender != 'non').first().format()
    actor_id = actor["id"]
    url = f'/actor/{actor_id}'
    surgeon = {'male': 'female', 'female': 'male'}
    new_gender = surgeon[actor['gender']]
    json = {'gender': new_gender}
    response = client.patch(url, json=json)
    assert response.status_code == 200
    respawned = Actor.query.get(actor['id'])
    # check that just the patched attribute has changed
    assert respawned.gender == new_gender
    assert respawned.name == actor['name']

    # fail with 404 actor id not in database
    # ---------------------------------------------------
    url = f'/actor/{BAD_ID}'
    response = client.patch(url)
    assert response.status_code == 404

    # fail with 422 bad data
    # -----------------------------------------------------
    url = f'/actor/{actor_id}'
    json = {'gender': 'bootylicious'}  # not a supported gender
    response = client.patch(url, json=json)
    assert response.status_code == 422


def test_patch_movie(client):
    # success
    # -------------------------------------------------
    # using .format so the attributes persist after session
    movie = Movie.query.first().format()
    movie_id = movie["id"]
    url = f'/movie/{movie_id}'
    new_title = movie['title'] + ' Part 2!!!'
    json = {'title': new_title}
    response = client.patch(url, json=json)
    assert response.status_code == 200
    respawned = Movie.query.get(movie['id'])
    # check that just the patched attribute has changed
    assert respawned.title.endswith('!!!')
    assert respawned.release_date == movie['release_date']

    # fail with 404 movie id not in database
    # ---------------------------------------------------
    url = f'/movie/{BAD_ID}'
    response = client.patch(url)
    assert response.status_code == 404

    # fail with 422 bad data
    # -----------------------------------------------------
    url = f'/movie/{movie_id}'
    json = {'release_date': 'twenty seventh'}  # needs to be a date
    response = client.patch(url, json=json)
    assert response.status_code == 422


def test_book_actor(client):
    # success
    # -------------------------------------------------
    actor_id = Actor.query.first().id
    role_id = Role.query.first().id
    url = f'/actor/{actor_id}/role/{role_id}'
    response = client.post(url)
    assert response.status_code == 200
    role = Role.query.get(role_id)
    assert role.filled
    actor = Actor.query.get(actor_id)
    assert actor.bookings

    # fail 404 one of the ids not found
    # -------------------------------------------------
    url = f'/actor/{actor_id}/role/{BAD_ID}'
    response = client.post(url)
    assert response.status_code == 404


def test_post_roles(client):
    # success
    # -------------------------------------------------
    movie = Movie.query.first()
    movie_id = movie.id
    nroles = len(movie.roles)  # this magically gives you a list of roles
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

    # fail with 404 movie not found
    # ---------------------------------------------------
    json = [{
        'name': 'Bystander D',
        'age': 40,
        'gender': 'female'
    }]
    response = client.post(f'/roles/{BAD_ID}', json=json)
    assert response.status_code == 404

    # fail with 422 all values required
    # ---------------------------------------------------
    json = [{
        'name': 'Bystander D',
        'gender': 'female'
    }]
    response = client.post(url, json=json)
    assert response.status_code == 422


def test_delete_roll(client):

    # success
    # --------------------------------------------------
    role_id = Role.query.first().id
    url = f'/role/{role_id}'
    response = client.delete(url)
    assert response.status_code == 200
    role = Role.query.get(role_id)
    assert role is None

    # fail with 404 role id not in database
    # -------------------------------------------------
    url = f'/role/{BAD_ID}'
    response = client.delete(url)
    assert response.status_code == 404


def test_patch_role(client):

    # sucess
    # --------------------------------------------------
    # using .format so the attributes persist after session
    role = Role.query.first().format()
    role_id = role["id"]
    url = f'/role/{role_id}'
    new_age = role['age'] + 10
    json = {'age': new_age}
    response = client.patch(url, json=json)
    assert response.status_code == 200
    respawned = Role.query.get(role['id'])
    # check that just the patched attribute has changed
    assert respawned.age == new_age
    assert respawned.name == role['name']

    # fail with 404 role id not in database
    # ---------------------------------------------------
    url = f'/role/{BAD_ID}'
    response = client.patch(url)
    assert response.status_code == 404

    # fail with 422 bad data
    # -----------------------------------------------------
    url = f'/role/{role_id}'
    json = {'age': 'twenty_seven'}  # needs to be a number
    response = client.patch(url, json=json)
    assert response.status_code == 422
