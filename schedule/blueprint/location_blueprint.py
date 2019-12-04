from flask import Blueprint, jsonify, request

from schedule.blueprint.decorators import admin_required, basic_auth
import schedule.db.database as database

import logging

from google.cloud import firestore

blueprint = Blueprint('bp_location', __name__)
db = firestore.Client()

logger = logging.getLogger(__name__)


@blueprint.route('', methods=['GET'])
@basic_auth
@admin_required
def locations(username=None):
    return jsonify({
        'locations': database.get_locations(),
        'status': 'ok'
    }), 200


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
    logger.info(f'getting {location_id} for {username}')

    location_obj = database.get_location(location_id)

    if location_obj is not None:
        return jsonify({
            'location': location_obj.to_dict(),
            'status': 'ok'
        }), 200
    else:
        logger.error(f'location {location_id} not found')
        return jsonify({
            'message': f'location {location_id} not found',
            'status': 'error'
        }), 404


def post_location(location_id, username):
    logger.info(f'updating {location_id} for {username}')

    location_obj = database.get_location(location_id)

    if location_obj is not None:

        # TODO add changes here

        return jsonify({
            'message': f'location {location_id} updated',
            'status': 'ok'
        }), 200
    else:
        logger.error(f'location {location_id} not found')
        return jsonify({
            'message': f'location {location_id} not found',
            'status': 'error'
        }), 404


def put_location(location_id, username):
    request_json = request.get_json()

    logger.info(f'creating location for {username}')

    try:
        database.create_location(location_id)
        return jsonify({
                'message': f'location {location_id} created',
                'status': 'ok'
            }), 200

    except FileExistsError:
        logger.error(f'location {location_id} already registered')
        return jsonify({
            'message': f'location {location_id} already registered',
            'status': 'error'
        }), 403


def delete_location(location_id, username):
    logger.info(f'deleting {location_id} for {username}')

    location_obj = database.get_location(location_id)

    if location_obj is not None:

        location_obj.db_ref.delete()

        return jsonify({
            'message': f'{location_id} deleted',
            'status': 'ok'
        }), 200
    else:
        logger.info(f'location {location_id} not found')
        return jsonify({
            'message': f'location {location_id} not found',
            'status': 'error'
        }), 404


@blueprint.route('/<location_id>/charger', methods=['GET'])
@basic_auth
def chargers(location_id, username=None):
    location_obj = database.get_location(location_id)
    if location_obj is not None:
        return jsonify({
            'chargers': [i.to_dict() for i in location_obj.chargers],
            'status': 'ok'
        }), 200
    else:
        return jsonify({
            'message': f'location {location_id} not found',
            'status': 'error'
        }), 404


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
    logger.info(f'getting {location_id}:{charger_id} for {username}')

    charger_obj = database.get_charger(location_id, charger_id)

    if charger_obj is not None:
        return jsonify({
            'charger': charger_obj.to_dict(),
            'status': 'ok'
        }), 200
    else:
        logger.error(f'charger {location_id}:{charger_id} not found')
        return jsonify({
            'message': f'charger {location_id}:{charger_id} not found',
            'status': 'error'
        }), 404


def post_charger(location_id, charger_id, username):
    logger.info(f'updating {location_id}:{charger_id} for {username}')

    charger_obj = database.get_charger(location_id, charger_id)

    if charger_obj is not None:

        # TODO add changes here

        return jsonify({
            'message': f'charger {location_id}:{charger_id} updated',
            'status': 'ok'
        }), 200
    else:
        logger.error(f'charger {location_id}:{charger_id} not found')
        return jsonify({
            'message': f'charger {location_id}:{charger_id} not found',
            'status': 'error'
        }), 404


def put_charger(location_id, charger_id, username):
    request_json = request.get_json()

    logger.info(f'creating charger for {username}')

    try:
        database.create_charger(location_id, charger_id)
        return jsonify({
            'message': f'charger {location_id}:{charger_id} created',
            'status': 'ok'
        }), 200

    except FileExistsError:
        logger.error(f'charger {location_id}:{charger_id} already registered')
        return jsonify({
            'message': f'charger {location_id}:{charger_id} already registered',
            'status': 'error'
        }), 403


def delete_charger(location_id, charger_id, username):
    logger.info(f'deleting {location_id}:{charger_id} for {username}')

    charger_obj = database.get_charger(location_id, charger_id)

    if charger_obj is not None:

        charger_obj.db_ref.delete()

        return jsonify({
            'message': f'{location_id}:{charger_id} deleted',
            'status': 'ok'
        }), 200
    else:
        logger.info(f'charger {location_id}:{charger_id} not found')
        return jsonify({
            'message': f'charger {location_id}:{charger_id} not found',
            'status': 'error'
        }), 404


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
