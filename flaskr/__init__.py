import os
from flask import Flask
from flask_cors import CORS
from .models import setup_db
from .controllers import register_views

def create_app(test_config=None):
    app = Flask(__name__)

    if test_config:
        app.config.from_mapping(test_config)
        dbpath = app.config.pop('DATABASE_URL')
    else:
        dbpath = os.environ['DATABASE_URL']
    setup_db(app, dbpath)

    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        return response

    register_views(app)

    return app
