from flask import Blueprint, jsonify, request

import logging

from google.cloud import firestore

blueprint = Blueprint('bp_location', __name__)
db = firestore.Client()

logger = logging.getLogger(__name__)


@blueprint.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def location(username=None):

    if request.method == 'GET':
        return get_location(username)
    elif request.method == 'POST':
        return post_location(username)
    elif request.method == 'PUT':
        return put_location(username)
    elif request.method == 'DELETE':
        return delete_location(username)


def get_location(username):
    return None


def post_location(username):
    return None


def put_location(username):
    return None


def delete_location(username):
    return None


@blueprint.route('/session', methods=['GET', 'POST', 'PUT', 'DELETE'])
def session(username=None):

    if request.method == 'GET':
        return get_session(username)
    elif request.method == 'POST':
        return post_session(username)
    elif request.method == 'PUT':
        return put_session(username)
    elif request.method == 'DELETE':
        return delete_session(username)


def get_session(username):
    return None


def post_session(username):
    return None


def put_session(username):
    return None


def delete_session(username):
    return None
