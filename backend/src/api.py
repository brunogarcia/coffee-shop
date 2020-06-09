import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

@app.after_request
def after_request(response):
    '''
    CORS Headers
    '''
    response.headers.add(
        'Access-Control-Allow-Headers',
        'Content-Type, Authorization, true'
    )
    response.headers.add(
        'Access-Control-Allow-Methods',
        'GET,PUT,POST, DELETE, OPTIONS'
    )

    return response

'''
Initialize the database
'''
db_drop_and_create_all()

## ROUTES
@app.route('/drinks', methods=['GET'])
def retrieve_drinks():
    '''
    Retrieve drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns
        status code 200
        json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    '''
    try:
        drinks = Drink.query.order_by(Drink.id).all()
        drinks_formatted = [
            drink.short() for drink in drinks
        ]

        return jsonify({
            'success': True,
            'drinks': drinks_formatted,
        })
    except Exception:
        abort(422)


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def retrieve_drinks_detail(payload):
    '''
        Retrieve drinks detail
            it should require the 'get:drinks-detail' permission
            it should contain the drink.long() data representation
        returns
            status code 200
            json {"success": True, "drinks": drinks}
                where drinks is the list of drinks
            or appropriate status code indicating reason for failure
    '''
    try:
        drinks = Drink.query.order_by(Drink.id).all()
        drinks_formatted = [
            drink.long() for drink in drinks
        ]

        return jsonify({
            'success': True,
            'drinks': drinks_formatted,
        })
    except Exception:
        abort(422)

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    '''
        Create a new drink
            it should create a new row in the drinks table
            it should require the 'post:drinks' permission
            it should contain the drink.long() data representation
        returns
            status code 200
            json {"success": True, "drinks": drink}
                where drink is an array containing only the newly created drink
            or appropriate status code indicating reason for failure
    '''
    # Get raw data
    body = request.get_json()
    recipe = body.get('recipe', None)
    title = body.get('title', None)

    try:
        # Create drink
        drink = Drink(
            title=title,
            recipe=json.dumps(recipe),
        )

        # Update db
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()],
        })
    except Exception:
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns
        status code 200
        json {"success": True, "drinks": drink}
        where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns
        status code 200
        json {"success": True, "delete": id}
        where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.errorhandler(400)
def bad_request():
    '''
    Handler for bad request
    '''
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400

@app.errorhandler(404)
def not_found():
    '''
    Handler for resource not found
    '''
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404

@app.errorhandler(422)
def unprocessable():
    '''
    Handler for unprocessable entity
    '''
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable entity"
    }), 422

@app.errorhandler(500)
def internal_server_error():
    '''
    Handler for internal server error
    '''
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500

@app.errorhandler(AuthError)
def auth_error(exception):
    '''
    Handler for AuthError
    '''
    return jsonify({
        "success": False,
        "error": exception.status_code,
        "code": exception.error['code'],
        "message": exception.error['description']
    }), exception.status_code
