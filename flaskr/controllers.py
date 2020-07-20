import sys
from functools import wraps
from dateutil.parser import parse
from werkzeug.exceptions import HTTPException
from flask import (request, jsonify, abort,
                   render_template, redirect, url_for)
from .models import Actor, Movie, Role, Booking, rollback, close_session, add_all
from .auth import AuthError, requires_auth_dummy
from .auth import requires_auth as requires_auth_
from .auth import register_views as reg_auth_views

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

PAGE_LENGTH = 10


def get_json():
    if request.json is None:
        abort(422, description='json required')
    return request.json

def commit_data(func):
    """Return the result of func.

    func -> commits data and optionally returns something
    Enforce the pattern
        try: commit func
        except: rollback, print error
        finally: close session
        if error: abort
    """
    error = False
    try:
        out = func()
    except Exception:
        error = True
        rollback()
        print(sys.exc_info())
    finally:
        close_session()
    if error:
        # @TODO maybe that's the message.  check the exceptions
        abort(422, description='Invalid data')
    return out


def get_paginate(model, query):
    # @TODO check out Model.paginate
    page = request.args.get('page', 1, type=int)
    page_length = request.args.get("page_length", PAGE_LENGTH, type=int)
    offset = (page - 1) * page_length

    if offset > query.count():
        abort(404, description=f'Page number {page} is out of bounds')
    results = query.limit(page_length).offset(offset)
    formatted_results = [r.format() for r in results]
    return jsonify({
        'success': True,
        model.plural(): formatted_results
    })


def post(model, column_names):
    column_vals = {}
    for kword in column_names:
        value = get_json().get(kword)
        if value is None:
            abort(422, description=f'{kword} required')
        column_vals[kword] = value

    def f():
        entry = model(**column_vals)
        entry.add()
        return entry.format()
    formatted_entry = commit_data(f)

    return jsonify({
        'success': True,
        model.singular(): formatted_entry
        })


def patch(model, id_, column_names):
    entry = model.query.get(id_)
    if entry is None:
        abort(404, description=f'{model.singular()} {id_} not found.')

    updates = {k: get_json()[k] for k in column_names if k in get_json()}

    def f():
        entry.update(updates)
        return entry.format()
    formatted_entry = commit_data(f)

    return jsonify({
        'success': True,
        model.singular(): formatted_entry
        })


def delete(model, id_):
    entry = model.query.get(id_)
    if entry is None:
        abort(404, description=f'{model.singular()} {id_} not found.')
    formatted_entry = entry.format()
    entry.delete()

    return jsonify({
        'success': True,
        model.singular(): formatted_entry
        })

def parse_gender(gender):
    g = gender.lower()
    return g if g in ['male', 'female'] else 'non'


def parse_age_range(age_range):
    try:
        lower, upper = map(int, age_range.split('-'))
        assert lower < upper
    except Exception:
        abort(422, description='Malformed age range')
    return lower, upper


def register_views(app):

    if app.config.get('TESTING_WITHOUT_AUTH'):
        requires_auth = requires_auth_dummy
    else:
        requires_auth = requires_auth_
    reg_auth_views(app)

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')

    @app.route('/actors', methods=['GET'])
    @requires_auth('view:actors')
    def actors(jwt_payload):
        # possible filters as url args:
        # gender: {male, female, non}
        # age: (inclusive range) <lower>-<upper>

        query = Actor.query
        # ---- gender -------------------------
        gender = request.args.get('gender')
        if gender:
            query = query.filter_by(gender=parse_gender(gender))
        # ---- age ----------------------------
        age = request.args.get('age')
        if age:
            lower, upper = parse_age_range(age)
            query = query.filter(Actor.age <= upper, Actor.age >= lower)
        return get_paginate(Actor, query)

    @app.route('/movies', methods=['GET'])
    @requires_auth('view:movies')
    def movies(jwt_payload):
        # @TODO think of something to order movies by
        # -- unfilled roles, start date is > today
        return get_paginate(Movie, Movie.query)

    @app.route('/actor', methods=['POST'])
    @requires_auth('add:actors')
    def post_actor(jwt_payload):
        return post(Actor, ['name', 'age', 'gender'])

    @app.route('/movie', methods=['POST'])
    @requires_auth('add:movies')
    def post_movie(jwt_payload):
        return post(Movie, ['title', 'release_date'])

    @app.route('/actor/<int:id_>', methods=['DELETE'])
    @requires_auth('delete:actors')
    def delete_actor(jwt_payload, id_):
        return delete(Actor, id_)

    @app.route('/movie/<int:id_>', methods=['DELETE'])
    @requires_auth('delete:movies')
    def delete_movie(jwt_payload, id_):
        return delete(Movie, id_)

    @app.route('/actor/<int:id_>', methods=['PATCH'])
    @requires_auth('edit:actors')
    def patch_actor(jwt_payload, id_):
        return patch(Actor, id_, ['name', 'age', 'gender'])

    @app.route('/role/<int:id_>', methods=['PATCH'])
    @requires_auth('edit:roles')
    def patch_role(jwt_payload, id_):
        return patch(Role, id_, ['name', 'age', 'gender', 'filled'])

    @app.route('/movie/<int:id_>', methods=['PATCH'])
    @requires_auth('edit:movies')
    def patch_movie(jwt_payload, id_):
        return patch(Movie, id_, ['title', 'release_date'])

    @app.route('/roles', methods=['GET'])
    @requires_auth('view:movies')
    def get_roles(jwt_payload):
        # possible filters as url args:
        # key word: domain
        # gender: {male, female, non}
        # age: (inclusive range) <lower>-<upper>
        # filled: {true, false}
        # start_date: date
        # end_date: date

        # check parms for correct form.
        filters = {}
        # ---- gender -------------------------

        gender = request.args.get('gender')
        if gender:
            filters['gender'] = parse_gender(gender)

        # ---- filled -------------------------
        filled = {'true':True, 'false':False}.get(request.args.get('filled', '').lower())
        if filled:
            filters['filled'] = filled

        # ---- age ----------------------------
        age = request.args.get('age')
        if age:
            lower, upper = parse_age_range(age)

        # ---- dates ---------------------------
        dates = request.args.get('start_date'), request.args.get('end_date')

        try:
            start_date, end_date = [parse(d) if d else None for d in dates]
        except Exception:
            abort(422, description='Malformed date range')

        if start_date and end_date and start_date >= end_date:
            abort(422, description='start_date must be before end_date')

        # ---- start filtering --------------------
        query = Role.query.filter_by(**filters)
        if age:
            query = query.filter(Role.age <= upper, Role.age >= lower)
        sub = Movie.query
        if start_date:
            sub = sub.filter(Movie.release_date > start_date)
        if end_date:
            sub = sub.filter(Movie.release_date < end_date)
        if start_date or end_date:
            query = query.join(sub.subquery())

        return get_paginate(Role, query)

    @app.route('/movie/<int:id_>', methods=['GET'])
    @requires_auth('view:movies')
    def get_movie(jwt_payload, id_):
        movie = Movie.query.get(id_)
        if movie is None:
            abort(404, description=f'Movie {id_} not found.')

        formatted_rolls = [r.format() for r in movie.roles]
        formatted_movie = movie.format()

        return jsonify({
            'success': True,
            'movie': formatted_movie,
            'roles': formatted_rolls
            })

    @app.route('/roles/<int:id_>', methods=['POST'])
    @requires_auth('add:roles')
    def post_roles(jwt_payload, id_):
        # requires json formatted as follows
        #
        # [
        #     {
        #         'name':name,
        #         'age':age,
        #         'gender':{'male, female, non'},
        #         'filled':bool (optional, defaults false)
        #     },...
        # ]
        roles = get_json()
        if not Movie.query.get(id_):
            abort(404, description=f'Movie {id_} not found')

        commit_data(
            lambda: add_all(
                [Role(movie_id=id_, **kwargs) for kwargs in roles]
            )
        )
        return jsonify({
            'success': True,
            'movie': id_,
            'num_roles': len(roles)
            })

    @app.route('/role/<int:id_>', methods=['DELETE'])
    @requires_auth('delete:roles')
    def delete_roll(jwt_payload, id_):
        return delete(Roll, id_)

    @app.route('/actor/<int:actor_id>/role/<int:role_id>', methods=['POST'])
    @requires_auth('book:actors')
    def book_actor(jwt_payload, actor_id, role_id):
        actor = Actor.query.get(actor_id)
        role = Role.query.get(role_id)
        if not (actor and role):
            abort(404, description='Actor or role not found')

        role.update(filled=True)
        commit_data(lambda: Booking(actor_id=actor_id, role_id=role_id).add())

        return jsonify({
            'success': True,
            'actor_id': actor_id,
            'role_id': role_id
            })

    def error_handler(error):
        return jsonify({
            'success': False,
            'description': error.description,
            'name': error.name,
            'status_code': error.code
            }), error.code

    app.register_error_handler(HTTPException, error_handler)
    app.register_error_handler(AuthError, error_handler)
