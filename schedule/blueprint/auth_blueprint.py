from flask import Blueprint, jsonify, request, redirect, url_for

import logging

from google.cloud import firestore

import schedule.db.database as database
from schedule.model.user import User

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
    if user.check_password(request_json['password']):
        return jsonify({
            'message': f'password match',
            'status': 'ok'
        }), 200
    else:
        return jsonify({
            'message': f'password mismatch',
            'status': 'error'
        }), 401


@blueprint.route('/logout', methods=['GET'])
def logout():

    response = {}
    return jsonify(response), 200
