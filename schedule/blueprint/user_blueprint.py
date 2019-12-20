from flask import Blueprint, request, jsonify

import logging

from google.cloud import firestore

import schedule.db.database as database
from schedule.blueprint.decorators import admin_required, url_arg_username_override, access_token
from schedule.model.user import User

blueprint = Blueprint('bp_user', __name__)
db = firestore.Client()

logger = logging.getLogger(__name__)


@blueprint.route('', methods=['GET', 'PUT'])
@access_token
@url_arg_username_override
def user(current_user: User = None):
    if request.method == 'GET':
        return get_user(current_user)
    elif request.method == 'PUT':
        return put_user(current_user)


@blueprint.route('', methods=['POST'])
@access_token
@admin_required
def user_restricted(current_user: User = None):
    if request.method == 'POST':
        return post_user(current_user)


@blueprint.route('', methods=['DELETE'])
@access_token
@admin_required
@url_arg_username_override
def user_restricted_with_override(current_user=None):
    if request.method == 'DELETE':
        return delete_user(current_user)


def get_user(current_user):
    logger.info(f'getting {current_user.username}')

    if current_user is not None:
        return jsonify({
            'user': current_user.to_dict(),
            'status': 'ok'
        }), 200
    else:
        logger.error(f'user {current_user.username} not found')
        return jsonify({
            'message': f'user {current_user.username} not found',
            'status': 'error'
        }), 404


def put_user(current_user):
    logger.info(f'updating {current_user.username}')

    if current_user is not None:

        request_json = request.get_json()

        if 'password' in request_json:
            if 'current_password' not in request_json:
                return jsonify({
                    'message': 'current_password must also be provided',
                    'status': 'error'
                }), 400

            if current_user.check_password(request_json['current_password']):
                logger.info(f'password updated for {current_user.username}')
                current_user.password = request_json['password']
            else:
                return jsonify({
                    'message': 'wrong password, no other updates made',
                    'status': 'error'
                }), 400

        if 'notification_token' in request_json:
            current_user.notification_token = request_json['notification_token']

        return jsonify({
            'message': f'user {current_user.username} updated',
            'status': 'ok'
        }), 200
    else:
        logger.error(f'user {current_user.username} not found')
        return jsonify({
            'message': f'user {current_user.username} not found',
            'status': 'error'
        }), 404


def post_user(current_user):
    request_json = request.get_json()

    logger.info(f'creating user for {current_user.username}')

    if 'username' not in request_json:
        logger.error(f'username not found to register user for {current_user.username}')
        return jsonify({
            'message': 'no username provided',
            'status': 'error'
        }), 400

    if 'password' not in request_json:
        logger.error(f'password not provided to register user for {current_user.username}')
        return jsonify({
            'message': 'no password provided',
            'status': 'error'
        }), 400

    try:
        database.create_user(username=request_json.get('username'),
                             password=request_json.get('password'),
                             user_type=User.Type[request_json.get('type', 'user')])
        return jsonify({
                'message': f'user {request_json.get("username")} created',
                'status': 'ok'
            }), 200

    except FileExistsError:
        logger.error(f'username {request_json["username"]} already registered')
        return jsonify({
            'message': f'username {request_json.get("username")} already registered',
            'status': 'error'
        }), 403


def delete_user(current_user):
    logger.info(f'deleting {current_user.username}')

    if current_user is not None:

        current_user.db_ref.delete()

        return jsonify({
            'message': f'{current_user.username} deleted',
            'status': 'ok'
        }), 200
    else:
        logger.info(f'user {current_user.username} not found')
        return jsonify({
            'message': f'user {current_user.username} not found',
            'status': 'error'
        }), 404
