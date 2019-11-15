from flask import Blueprint, jsonify, request

from schedule.blueprint.decorators import admin_required, basic_auth

import logging

from google.cloud import firestore

blueprint = Blueprint('bp_location', __name__)
db = firestore.Client()

logger = logging.getLogger(__name__)


@blueprint.route('', methods=['GET'])
@basic_auth
@admin_required
def locations(username=None):
    return None


@blueprint.route('/<location_id>', methods=['GET'])
@basic_auth
def location(location_id, username=None):
    if request.method == 'GET':
        return get_location(location_id, username)


@blueprint.route('/<location_id>', methods=['POST', 'PUT', 'DELETE'])
@basic_auth
@admin_required
def location_restricted(location_id, username=None):
    if request.method == 'POST':
        return post_location(location_id, username)
    elif request.method == 'PUT':
        return put_location(location_id, username)
    elif request.method == 'DELETE':
        return delete_location(location_id, username)


def get_location(location_id, username):
    return None


def post_location(location_id, username):
    return None


def put_location(location_id, username):
    return None


def delete_location(location_id, username):
    return None


@blueprint.route('/<location_id>/charger', methods=['GET'])
@basic_auth
def chargers(location_id, username=None):
    return None


@blueprint.route('/<location_id>/charger/<charger_id>', methods=['GET'])
@basic_auth
def charger(location_id, charger_id, username=None):
    if request.method == 'GET':
        return get_charger(location_id, charger_id, username)


@blueprint.route('/<location_id>/charger/<charger_id>', methods=['POST', 'PUT', 'DELETE'])
@basic_auth
@admin_required
def charger_restricted(location_id, charger_id, username=None):
    if request.method == 'POST':
        return post_charger(location_id, charger_id, username)
    elif request.method == 'PUT':
        return put_charger(location_id, charger_id, username)
    elif request.method == 'DELETE':
        return delete_charger(location_id, charger_id, username)


def get_charger(location_id, charger_id, username):
    return None


def post_charger(location_id, charger_id, username):
    return None


def put_charger(location_id, charger_id, username):
    return None


def delete_charger(location_id, charger_id, username):
    return None


@blueprint.route('/<location_id>/charger/<charger_id>/session', methods=['GET'])
def session(location_id, charger_id, username=None):
    if request.method == 'GET':
        return get_session(location_id, charger_id, username)


@blueprint.route('/<location_id>/charger/<charger_id>/session', methods=['POST', 'PUT', 'DELETE'])
def session_restricted(location_id, charger_id, username=None):
    if request.method == 'POST':
        return post_session(location_id, charger_id, username)
    elif request.method == 'PUT':
        return put_session(location_id, charger_id, username)
    elif request.method == 'DELETE':
        return delete_session(location_id, charger_id, username)


def get_session(location_id, charger_id, username):
    return None


def post_session(location_id, charger_id, username):
    return None


def put_session(location_id, charger_id, username):
    return None


def delete_session(location_id, charger_id, username):
    return None
