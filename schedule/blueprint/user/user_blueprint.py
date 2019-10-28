from flask import Blueprint, request, jsonify

import logging

from google.cloud import firestore

import schedule.db.database as database
import schedule.interface.interface as interface

blueprint = Blueprint('bp_user', __name__)
db = firestore.Client()

logger = logging.getLogger(__name__)


@blueprint.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def user(username=None):

    if request.method == 'GET':
        return get_user(username)
    elif request.method == 'POST':
        return post_user(username)
    elif request.method == 'PUT':
        return put_user(username)
    elif request.method == 'DELETE':
        return delete_user(username)


def get_user(username: str):
    if request.args.get('username'):
        username = request.args.get('username')

    user_obj = database.get_user(username)

    if user_obj is not None:
        return jsonify(interface.create_response({
            'user': user_obj.to_dict()
        }, success=True)), 200
    else:
        return jsonify(interface.create_response({
            'error': f'user {username} not found'
        }, error=True)), 404


def post_user(username):
    if request.args.get('username'):
        username = request.args.get('username')

    user_obj = database.get_user(username)

    if user_obj is not None:

        # TODO make user updates

        return jsonify(interface.create_response({
            'message': f'user {username} updated'
        }, success=True)), 200
    else:
        return jsonify(interface.create_response({
            'error': f'user {username} not found'
        }, error=True)), 404


def put_user(username):
    request_json = request.get_json()

    if 'username' not in request_json:
        return jsonify(interface.create_response({
            'error': 'no username provided'
        }, error=True)), 400

    users = [i for i in db.collection(u'user').where(u'username', u'==', request_json.get('username')).stream()]

    if len(users) > 0:
        return jsonify(interface.create_response({
            'error': f'username {request_json.get("username")} already registered'
        }, error=True)), 403

    database.create_user(request_json.get('username'))
    return jsonify(interface.create_response({
            'message': f'user {request_json.get("username")} created'
        }, success=True)), 200


def delete_user(username):
    return None


@blueprint.route('/vehicle', methods=['GET', 'POST', 'PUT', 'DELETE'])
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
