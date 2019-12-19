from flask import Blueprint, jsonify, request

from schedule.blueprint.decorators import admin_required, access_token, access_token
import schedule.db.database as database
from schedule.model.location import Charger
from schedule.model.user import User

import logging

from google.cloud import firestore

blueprint = Blueprint('bp_location', __name__)
db = firestore.Client()

logger = logging.getLogger(__name__)


@blueprint.route('', methods=['GET'])
@access_token
@admin_required
def locations(current_user: User = None):
    pulled = database.get_locations()

    if locations is not None:
        return jsonify({
            'locations': [i.to_dict() for i in pulled],
            'status': 'ok'
        }), 200
    return jsonify({
        'message': 'no locations found',
        'status': 'ok'
    }), 503


@blueprint.route('/<location_id>', methods=['GET'])
@access_token
def location(location_id, current_user: User = None):
    if request.method == 'GET':
        return get_location(location_id, current_user)


@blueprint.route('/<location_id>', methods=['PUT', 'POST', 'DELETE'])
@access_token
@admin_required
def location_restricted(location_id, current_user: User = None):
    if request.method == 'PUT':
        return put_location(location_id, current_user)
    elif request.method == 'POST':
        return post_location(location_id, current_user)
    elif request.method == 'DELETE':
        return delete_location(location_id, current_user)


def get_location(location_id, current_user):
    logger.info(f'getting {location_id} for {current_user}')

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


def put_location(location_id, current_user):
    logger.info(f'updating {location_id} for {current_user}')

    location_obj = database.get_location(location_id)

    if location_obj is not None:

        # TODO add manipulations here

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


def post_location(location_id, current_user):
    request_json = request.get_json()

    logger.info(f'creating location for {current_user}')

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
    except ValueError:
        logger.error(f'illegal character present in {location_id}')
        return jsonify({
            'message': f'illegal character present in {location_id}',
            'status': 'error'
        }), 400


def delete_location(location_id, current_user):
    logger.info(f'deleting {location_id} for {current_user}')

    location_obj = database.get_location(location_id)

    if location_obj is not None:

        database.delete_location(location_id)

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
@access_token
def chargers(location_id, current_user: User = None):
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
@access_token
def charger(location_id, charger_id, current_user: User = None):
    if request.method == 'GET':
        return get_charger(location_id, charger_id, current_user)


@blueprint.route('/<location_id>/charger/<charger_id>', methods=['PUT', 'POST', 'DELETE'])
@access_token
@admin_required
def charger_restricted(location_id, charger_id, current_user: User = None):
    if request.method == 'PUT':
        return put_charger(location_id, charger_id, current_user)
    elif request.method == 'POST':
        return post_charger(location_id, charger_id, current_user)
    elif request.method == 'DELETE':
        return delete_charger(location_id, charger_id, current_user)


def get_charger(location_id, charger_id, current_user):
    logger.info(f'getting {location_id}:{charger_id} for {current_user}')

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


def put_charger(location_id, charger_id, current_user):
    logger.info(f'updating {location_id}:{charger_id} for {current_user}')

    charger_obj = database.get_charger(location_id, charger_id)

    if charger_obj is not None:

        request_json = request.get_json()

        if charger_obj.active_session is not None:
            if current_user.user_type == User.Type.service:
                if 'state' in request_json:
                    try:
                        new_state = Charger.State[request_json['state'].lower()]
                        if charger_obj.state == Charger.State.available and new_state == Charger.State.pre_session:
                            logger.error(f'sessions must be started from the queue ({current_user}) '
                                         f'{location_id}:{charger_id}:{charger_obj.active_session}')
                            return jsonify({
                                'message': f'sessions must be started from the queue '
                                           f'{location_id}:{charger_id}:{charger_obj.active_session}',
                                'status': 'error'
                            }), 400
                        elif charger_obj.state == Charger.State.full and new_state == Charger.State.available:
                            logger.error(f'sessions must be ended from the queue ({current_user}) '
                                         f'{location_id}:{charger_id}:{charger_obj.active_session}')
                            return jsonify({
                                'message': f'sessions must be ended from the queue '
                                           f'{location_id}:{charger_id}:{charger_obj.active_session}',
                                'status': 'error'
                            }), 400
                        charger_obj.state = new_state

                    except KeyError:
                        logger.error(f'{request_json["state"]} is not a valid charger state ({current_user}) '
                                     f'{location_id}:{charger_id}:{charger_obj.active_session}')
                        return jsonify({
                            'message': f'{request_json["state"]} is not a valid charger state '
                                       f'{location_id}:{charger_id}:{charger_obj.active_session}',
                            'status': 'error'
                        }), 400
                    except SystemError:
                        logger.error(f'{Charger.state} to {request_json["state"]} is not a valid state change '
                                     f'({current_user}) {location_id}:{charger_id}:{charger_obj.active_session}')
                        return jsonify({
                            'message': f'{request_json["state"]} is not a valid charger state '
                                       f'{location_id}:{charger_id}:{charger_obj.active_session}',
                            'status': 'error'
                        }), 400
            else:
                logger.error(f'{current_user} is not a service account '
                             f'{location_id}:{charger_id}:{charger_obj.active_session}')
                return jsonify({
                    'message': f'{current_user} is not a service account',
                    'status': 'error'
                }), 400
        else:
            logger.error(f'no session running at {location_id}:{charger_id}')
            return jsonify({
                'message': f'no session running at {location_id}:{charger_id}',
                'status': 'error'
            }), 400

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


def post_charger(location_id, charger_id, current_user):
    request_json = request.get_json()

    logger.info(f'creating {location_id}:{charger_id} charger for {current_user}')

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
    except ValueError:
        logger.error(f'illegal character present in {charger_id}')
        return jsonify({
            'message': f'illegal character present in {charger_id}',
            'status': 'error'
        }), 400


def delete_charger(location_id, charger_id, current_user):
    logger.info(f'deleting {location_id}:{charger_id} for {current_user}')

    charger_obj = database.get_charger(location_id, charger_id)

    if charger_obj is not None:

        database.delete_charger(location_id, charger_id)

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
@access_token
def session(location_id, charger_id, current_user: User = None):
    if request.method == 'GET':
        return get_session(location_id, charger_id, current_user)


@blueprint.route('/<location_id>/charger/<charger_id>/session', methods=['PUT', 'POST', 'DELETE'])
@access_token
@admin_required
def session_restricted(location_id, charger_id, current_user: User = None):
    if request.method == 'PUT':
        return put_session(location_id, charger_id, current_user)
    elif request.method == 'POST':
        return post_session(location_id, charger_id, current_user)
    elif request.method == 'DELETE':
        return delete_session(location_id, charger_id, current_user)


def get_session(location_id, charger_id, current_user):
    logger.info(f'getting {location_id}:{charger_id} session for {current_user}')

    session_obj = database.get_active_session(location_id, charger_id)

    if session_obj is not None:
        return jsonify({
            'session': session_obj.to_dict(),
            'status': 'ok'
        }), 200
    else:
        logger.error(f'no active session at {location_id}:{charger_id}')
        return jsonify({
            'message': f'{location_id}:{charger_id} active session not found',
            'status': 'error'
        }), 404


def put_session(location_id, charger_id, current_user):
    logger.info(f'updating {location_id}:{charger_id} session for {current_user}')

    session_obj = database.get_active_session(location_id, charger_id)

    if session_obj is not None:

        return jsonify({
            'message': f'active session {location_id}:{charger_id} updated',
            'status': 'ok'
        }), 200
    else:
        logger.error(f'no active session at {location_id}:{charger_id}')
        return jsonify({
            'message': f'{location_id}:{charger_id} active session not found',
            'status': 'error'
        }), 404


def post_session(location_id, charger_id, current_user):
    request_json = request.get_json()

    if current_user.user_type == User.Type.service and request_json is not None and 'username' in request_json:
        current_user = database.get_user(request_json.get('username'))

    logger.info(f'starting session at {location_id}:{charger_id} for {current_user}')

    try:
        location_obj = database.get_location(location_id)
        if location_obj is not None:
            database.queue_user(location_id, current_user)
            return jsonify({
                'message': f'{current_user} queued at {location_id}',
                'status': 'ok'
            }), 200
        else:
            logger.error(f'location {location_id} not found')
            return jsonify({
                'message': f'location {location_id} not found',
                'status': 'error'
            }), 404

    except FileExistsError:
        logger.error(f'session already running at {location_id}:{charger_id}')
        return jsonify({
            'message': f'session already running at {location_id}:{charger_id}',
            'status': 'error'
        }), 403
    except FileNotFoundError:
        logger.error(f'charger {location_id}:{charger_id} not found')
        return jsonify({
            'message': f'charger {location_id}:{charger_id} not found',
            'status': 'error'
        }), 404


def delete_session(location_id, charger_id, current_user):
    logger.info(f'stopping session at {location_id}:{charger_id} for {current_user}')

    try:
        active_session = database.get_active_session(location_id, charger_id)

        if active_session.user == current_user or current_user.user_type == User.Type.service:
            database.end_session(location_id, charger_id)
            return jsonify({
                'message': f'{location_id}:{charger_id} session stopped',
                'status': 'ok'
            }), 200
        else:
            logger.info(f'{current_user} does not own this session {location_id}:{charger_id}:{active_session.session_id}')
            return jsonify({
                'message': f'{current_user} does not own this session',
                'status': 'error'
            }), 404

    except FileNotFoundError:
        logger.info(f'no session running at {location_id}:{charger_id}')
        return jsonify({
            'message': f'no session running at {location_id}:{charger_id}',
            'status': 'error'
        }), 404


@blueprint.route('/<location_id>/queue', methods=['POST', 'DELETE'])
@access_token
def queue(location_id, current_user: User = None):
    if request.method == 'POST':
        return post_queue(location_id, current_user)
    elif request.method == 'DELETE':
        return delete_queue(location_id, current_user)


def post_queue(location_id,  current_user):
    logger.info(f'adding {current_user} to {location_id} queue')

    location_obj = database.get_location(location_id)

    if location_obj is not None:
        if current_user.username not in [i.username for i in location_obj.queue]:
            database.queue_user(location_id, current_user)

            return jsonify({
                'message': f'{current_user} queued for {location_id}',
                'status': 'ok'
            }), 200
        else:
            logger.error(f'{current_user} not queued for {location_id}')
            return jsonify({
                'message': f'{current_user} not queued for {location_id}',
                'status': 'error'
            }), 404
    else:
        logger.error(f'location {location_id} not found')
        return jsonify({
            'message': f'location {location_id} not found',
            'status': 'error'
        }), 404


def delete_queue(location_id,  current_user):
    logger.info(f'adding {current_user} to {location_id} queue')

    location_obj = database.get_location(location_id)

    if location_obj is not None:
        if current_user.username in [i.username for i in location_obj.queue]:
            database.remove_user_from_queue(location_id, current_user)
            return jsonify({
                'message': f'{current_user} removed from {location_id} queue',
                'status': 'ok'
            }), 200

        else:
            logger.error(f'{current_user} not queued for {location_id}')
            return jsonify({
                'message': f'{current_user} not queued for {location_id}',
                'status': 'error'
            }), 404
    else:
        logger.error(f'location {location_id} not found')
        return jsonify({
            'message': f'location {location_id} not found',
            'status': 'error'
        }), 404
