from flask import Blueprint, jsonify, request

import logging

from google.cloud import firestore

import schedule.db.database as database
from schedule.blueprint.decorators import access_token

blueprint = Blueprint('bp_auth', __name__)
db = firestore.Client()

logger = logging.getLogger(__name__)


@blueprint.route('/login', methods=['POST'])
def login():
    request_json = request.get_json()

    if 'username' not in request_json:
        logger.error(f'username not provided')
        return jsonify({
            'message': 'no username provided',
            'status': 'error'
        }), 400

    if 'password' not in request_json:
        logger.error(f'password not provided')
        return jsonify({
            'message': 'no password provided',
            'status': 'error'
        }), 400

    user = database.get_user(request_json['username'])
    if user is not None:
        if user.check_password(request_json['password']):
            if user.access_token is None:
                user.refresh_access_token()

            return jsonify({
                'message': 'password match',
                'token': user.access_token,
                'status': 'ok'
            }), 200
        else:
            return jsonify({
                'message': 'password mismatch',
                'status': 'error'
            }), 401
    else:
        return jsonify({
            'message': 'username not found',
            'status': 'error'
        }), 404


@blueprint.route('/logout', methods=['GET'])
@access_token
def logout(current_user=None):
    current_user.access_token = None
    return jsonify({
        'message': 'user logged out',
        'status': 'ok'
    }), 200
