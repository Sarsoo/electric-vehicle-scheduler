import functools
import logging

from flask import request, jsonify

import schedule.db.database as database
from schedule.model.user import User


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


def get_basic_auth_user():
    if request.authorization:
        if request.authorization.get('username', None) and request.authorization.get('password', None):
            basic_auth_user = database.get_user(request.authorization.username)
            if basic_auth_user.check_password(request.authorization.password):
                return basic_auth_user

    return None


def get_token_user():
    header = request.headers.get('Authorization')
    if header is not None:
        if header.startswith('Bearer '):
            token = header.strip('Bearer ')
            return next((i for i in database.get_users() if i.access_token == token), None)

    return None


def basic_auth(func):
    @functools.wraps(func)
    def basic_auth_wrapper(*args, **kwargs):
        print(request.headers)
        basic_auth_user = get_basic_auth_user()
        if basic_auth_user is not None:
            return func(current_user=basic_auth_user, *args, **kwargs)
        else:
            logger.warning('user not logged in')
            return jsonify({'status': 'error', 'message': 'not logged in'}), 401

    return basic_auth_wrapper


def access_token(func):
    @functools.wraps(func)
    def access_token_wrapper(*args, **kwargs):
        token_user = get_token_user()
        if token_user is not None:
            return func(current_user=token_user, *args, **kwargs)
        else:
            logger.warning('invalid key')
            return jsonify({'status': 'error', 'message': 'invalid key'}), 401

    return access_token_wrapper


def admin_required(func):
    @functools.wraps(func)
    def admin_required_wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')

        if current_user is not None:
            if current_user.user_type == current_user.Type.admin:
                return func(*args, **kwargs)
            else:
                logger.warning(f'{current_user.username} not authorized')
                return jsonify({'status': 'error', 'message': 'unauthorized'}), 401
        else:
            logger.warning('user not logged in')
            return jsonify({'status': 'error', 'message': 'not logged in'}), 401

    return admin_required_wrapper


def url_arg_username_override(func):
    @functools.wraps(func)
    def url_arg_username_override_wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')

        if current_user.user_type == User.Type.admin:
            if request.args.get('username'):
                logger.info(f'overriding username to {request.args.get("username")} for {current_user.username}')
                del kwargs['current_user']
                return func(current_user=database.get_user(request.args.get('username')), *args, **kwargs)

        return func(*args, **kwargs)

    return url_arg_username_override_wrapper
