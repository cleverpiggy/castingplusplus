from os import environ
from functools import wraps
import json
from flask import redirect, url_for, jsonify, request
from dotenv import load_dotenv, find_dotenv

# @TODO see if I can just use from urllib import urlencode, url open
# to avoid the six dependancy
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import urlopen
from jose import jwt

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

AUTH0_CALLBACK_URL = environ.get('AUTH0_CALLBACK_URL')
AUTH0_CLIENT_ID = environ.get('AUTH0_CLIENT_ID')
AUTH0_DOMAIN = environ.get('AUTH0_DOMAIN')
AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
AUTH0_AUDIENCE = environ.get('AUTH0_AUDIENCE')

ALGORITHMS = ["RS256"]


class AuthError(Exception):
    def __init__(self, name, description, code=401):
        self.name = name
        self.description = description
        self.code = code


# Format error response and append status code
def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError(
            name="authorization_header_missing",
            description="Authorization header is expected"
        )

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError(
            name="invalid_header",
            description="Authorization header must start with Bearer"
        )
    if len(parts) == 1:
        raise AuthError(
            name="invalid_header",
            description="Token not found"
        )
    if len(parts) > 2:
        raise AuthError(
            name="invalid_header",
            description="Authorization header must be"
                        " Bearer token"
        )

    token = parts[1]
    return token


def verify_decode_jwt(token):
    """
    Return a dictionary of the encoded information.

    Raise an error if the token is invalid in any way.
    """
    jsonurl = urlopen("https://" + AUTH0_DOMAIN + "/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception:
        raise AuthError(
            name="invalid_header",
            description="Authorization malformed."
        )
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError(
            name='invalid_header',
            description='Authorization malformed.'
        )
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if not rsa_key:
        raise AuthError(
            name="invalid_header",
            description="Unable to find appropriate key"
        )
    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer="https://" + AUTH0_DOMAIN + "/"
        )
    except jwt.ExpiredSignatureError:
        raise AuthError(
            name="token_expired",
            description="token is expired"
        )
    except jwt.JWTClaimsError:
        raise AuthError(
            name="invalid_claims",
            description="incorrect claims,"
                        "please check the audience and issuer"
            )
    except Exception:
        raise AuthError(
            name="invalid_header",
            description="Unable to parse authentication token."
        )
    return payload


def check_permissions(permission, payload):
    if not permission:
        return True
    permissions = payload.get('permissions')
    if permissions is None:
        raise AuthError(
            name='invalid_claims',
            description='Permissions not included in JWT.'
        )
    if permission not in permissions:
        raise AuthError(
            name='invalid_claims',
            description='Permission not found.'
        )
    return True


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator


# used for testing functionality ignoring authorization
def requires_auth_dummy(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f({}, *args, **kwargs)
        return wrapper
    return requires_auth_decorator


def register_views(app):

    # @TODO state is about mitigating a CSRF attack by attaching some random info,
    # store it on the client side (sessions), and AUTH0 will return the same string to check against
    # https://en.wikipedia.org/wiki/Cross-site_request_forgery
    # scope needs to be appended to authorize_url for /userinfo to work
    authorize_url = f"https://{AUTH0_DOMAIN}/authorize?audience={AUTH0_AUDIENCE}&response_type=token&client_id={AUTH0_CLIENT_ID}&redirect_uri={AUTH0_CALLBACK_URL}"

    @app.route('/callback')
    def callback():
        # Handles response from token endpoint
        return redirect(url_for('index'))

    @app.route('/login', methods=['POST', 'GET'])
    def login():
        # https://auth0.com/docs/universal-login/default-login-url?_ga=2.99410717.2004209071.1594001273-1129603475.1594001273
        # The login_url should point to a route in the application that ends up
        # redirecting to Auth0's /authorize endpoint, e.g. https://mycompany.org/login.
        # Note that it requires https and it cannot point to localhost.
        return redirect(authorize_url)

    @app.route('/verify<token>', methods=['GET'])
    def verify_decode_route(token):
        payload = verify_decode_jwt(token)
        return jsonify({
            'permissions': payload['permissions'],
            'success': True
        })

    @app.route('/logout')
    def logout():
        # Redirect user to logout endpoint
        params = {'returnTo': url_for('index', _external=True), 'client_id': AUTH0_CLIENT_ID}
        return redirect(AUTH0_BASE_URL + '/v2/logout?' + urlencode(params))

    #     # 1. clear the session cookies (N/A)
    #     # 2. log out with auth0 api
    #     # https://YOUR_DOMAIN/v2/logout
