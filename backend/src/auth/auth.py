"""
Auth support
"""
import json
from urllib.request import urlopen
from functools import wraps
from flask import request, abort
from jose import jwt


AUTH0_DOMAIN = 'brunogarcia.eu.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffe-shop'

BEARER = 'bearer'
PERMISSIONS = 'permissions'
AUTHORIZATION = 'Authorization'

## AuthError Exception
class AuthError(Exception):
    '''
    AuthError Exception
    A standardized way to communicate auth failure modes
    '''
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

def get_token_auth_header():
    '''
    Get token auth header
    It should attempt to get the Authorization header from the request
        if no Authorization header is present
        should raise an AuthError (401)
    It should attempt to split bearer and the token
        if the Authorization header is malformed
        should raise an AuthError (401)
    Return the token part of the header
    '''
    auth = request.headers.get(AUTHORIZATION, None)
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    parts = auth.split()
    if parts[0].lower() != BEARER:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)

    if len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    if len(parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    token = parts[1]

    return token

def check_permissions(permission, payload):
    '''
    Check permissions
        @INPUTS
            permission: string permission (i.e. 'post:drink')
            payload: decoded jwt payload

        It should raise an AuthError 400:
            if permissions are not included in the payload
            note: check the RBAC settings in Auth0

        It should raise an AuthError 403:
            if the requested permission string
            is not in the payload permissions array

        Return true otherwise
    '''
    if PERMISSIONS not in payload:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT.'
        }, 400)

    if permission not in payload[PERMISSIONS]:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 403)

    return True

def verify_decode_jwt(token):
    '''
    Verify decode JWT
        @INPUTS
            token: a json web token (string)

        it should be an Auth0 token with key id (kid)
        it should verify the token using Auth0 /.well-known/jwks.json
        it should decode the payload from the token
        it should validate the claims
        return the decoded payload

        note:
            urlopen has a common certificate error described here
            https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
    '''
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}

    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)

        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)

    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key.'
    }, 400)

def requires_auth(permission=''):
    '''
    Requires auth decorator
        @INPUTS
            permission: string permission (i.e. 'post:drink')

        Use the get_token_auth_header method to get the token
        Use the verify_decode_jwt method to decode the jwt
        Use the check_permissions method validate claims
        And check the requested permission
        Return the decorator which passes the decoded payload to the decorated method
    '''
    def requires_auth_decorator(function_to_decorate):
        @wraps(function_to_decorate)
        def wrapper(*args, **kwargs):
            try:
                token = get_token_auth_header()
                payload = verify_decode_jwt(token)
            except Exception as error:
                print(error)
                abort(401)

            check_permissions(permission, payload)
            return function_to_decorate(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
