from flask import Blueprint, request, jsonify

import logging

from google.cloud import firestore

import schedule.db.database as database
from schedule.blueprint.decorators import basic_auth, admin_required
from schedule.model.user import User

blueprint = Blueprint('bp_user', __name__)
db = firestore.Client()

logger = logging.getLogger(__name__)


@blueprint.route('', methods=['GET', 'POST'])
@basic_auth
def user(username=None):
    if request.method == 'GET':
        return get_user(username)
    elif request.method == 'POST':
        return post_user(username)


@blueprint.route('', methods=['PUT', 'DELETE'])
@basic_auth
@admin_required
def user_restricted(username=None):
    if request.method == 'PUT':
        return put_user(username)
    elif request.method == 'DELETE':
        return delete_user(username)


def get_user(username: str):

    if database.get_user(username).user_type == User.Type.admin:
        if request.args.get('username'):
            username = request.args.get('username')

    user_obj = database.get_user(username)

    if user_obj is not None:
        return jsonify({
            'user': user_obj.to_dict(),
            'status': 'ok'
        }), 200
    else:
        return jsonify({
            'message': f'user {username} not found',
            'status': 'error'
        }), 404


def post_user(username):

    if database.get_user(username).user_type == User.Type.admin:
        if request.args.get('username'):
            username = request.args.get('username')

    user_obj = database.get_user(username)

    if user_obj is not None:

        request_json = request.get_json()

        if 'password' in request_json:
            if 'current_password' not in request_json:
                return jsonify({
                    'message': 'current_password must also be provided',
                    'status': 'error'
                }), 400

            if user_obj.check_password(request_json['current_password']):
                user_obj.password = request_json['password']
            else:
                return jsonify({
                    'message': 'wrong password, no other updates made',
                    'status': 'error'
                }), 400

        return jsonify({
            'message': f'user {username} updated',
            'status': 'ok'
        }), 200
    else:
        return jsonify({
            'message': f'user {username} not found',
            'status': 'error'
        }), 404


def put_user(username):
    request_json = request.get_json()

    if 'username' not in request_json:
        return jsonify({
            'message': 'no username provided',
            'status': 'error'
        }), 400

    if 'password' not in request_json:
        return jsonify({
            'message': 'no password provided',
            'status': 'error'
        }), 400

    users = [i for i in db.collection(u'user').where(u'username', u'==', request_json.get('username')).stream()]

    if len(users) > 0:
        return jsonify({
            'message': f'username {request_json.get("username")} already registered',
            'status': 'error'
        }), 403

    database.create_user(username=request_json.get('username'),
                         password=request_json.get('password'),
                         user_type=User.Type[request_json.get('type', 'user')])
    return jsonify({
            'message': f'user {request_json.get("username")} created',
            'status': 'ok'
        }), 200


def delete_user(username):
    if request.args.get('username'):
        username = request.args.get('username')

    user_obj = database.get_user(username)

    if user_obj is not None:

        user_obj.db_ref.delete()

        return jsonify({
            'message': f'{username} deleted',
            'status': 'ok'
        }), 200
    else:
        return jsonify({
            'message': f'user {username} not found',
            'status': 'error'
        }), 404


# @blueprint.route('/vehicle', methods=['GET', 'POST', 'PUT', 'DELETE'])
def vehicle(username=None):

    if request.method == 'GET':
        return get_vehicle(username)
    elif request.method == 'POST':
        return post_vehicle(username)
    elif request.method == 'PUT':
        return put_vehicle(username)
    elif request.method == 'DELETE':
        return delete_vehicle(username)


def get_vehicle(username):
    return None


def post_vehicle(username):
    return None


def put_vehicle(username):
    return None


def delete_vehicle(username):
    return None
