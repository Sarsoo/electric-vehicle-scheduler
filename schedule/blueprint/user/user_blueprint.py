from flask import Blueprint, request, jsonify

import logging

from google.cloud import firestore

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


def get_user(username):
    return None


def post_user(username):
    return None


def put_user(username):
    return None


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
