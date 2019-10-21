from flask import Blueprint, jsonify

import logging

from google.cloud import firestore

blueprint = Blueprint('bp_auth', __name__)
db = firestore.Client()

logger = logging.getLogger(__name__)


@blueprint.route('/login', methods=['GET'])
def login(username=None):

    response = {}
    return jsonify(response), 200


@blueprint.route('/logout', methods=['GET'])
def logout(username=None):

    response = {}
    return jsonify(response), 200


@blueprint.route('/register', methods=['GET'])
def register(username=None):

    response = {}
    return jsonify(response), 200
