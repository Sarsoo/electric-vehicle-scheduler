import functools
import logging

from flask import request, jsonify

import schedule.db.database as database


logger = logging.getLogger(__name__)


def gae_cron(func):
    @functools.wraps(func)
    def gae_cron_wrapper(*args, **kwargs):

        if request.headers.get('X-Appengine-Cron', None):
            return func(*args, **kwargs)
        else:
            logger.warning('user not logged in')
            return jsonify({'status': 'error', 'message': 'unauthorised'}), 401

    return gae_cron_wrapper


def cloud_task(func):
    @functools.wraps(func)
    def cloud_task_wrapper(*args, **kwargs):

        if request.headers.get('X-AppEngine-QueueName', None):
            return func(*args, **kwargs)
        else:
            logger.warning('non tasks request')
            return jsonify({'status': 'error', 'message': 'unauthorised'}), 401

    return cloud_task_wrapper


def is_basic_authed():
    if request.authorization:
        if request.authorization.get('username', None) and request.authorization.get('password', None):
            if database.get_user(request.authorization.username).check_password(request.authorization.password):
                return True

    return False


def basic_auth(func):
    @functools.wraps(func)
    def basic_auth_wrapper(*args, **kwargs):
        if is_basic_authed():
            return func(username=request.authorization.username, *args, **kwargs)
        else:
            logger.warning('user not logged in')
            return jsonify({'status': 'error', 'message': 'not logged in'}), 401

    return basic_auth_wrapper


def admin_required(func):
    @functools.wraps(func)
    def admin_required_wrapper(*args, **kwargs):
        db_user = database.get_user(kwargs.get('username'))

        if db_user is not None:
            if db_user.user_type == db_user.Type.admin:
                return func(*args, **kwargs)
            else:
                logger.warning(f'{db_user.username} not authorized')
                return jsonify({'status': 'error', 'message': 'unauthorized'}), 401
        else:
            logger.warning('user not logged in')
            return jsonify({'status': 'error', 'message': 'not logged in'}), 401

    return admin_required_wrapper
