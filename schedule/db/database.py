from google.cloud import firestore
import logging
from typing import Optional

from schedule.model.user import User
from schedule.model.location import Location

from werkzeug.security import generate_password_hash

db = firestore.Client()
logger = logging.getLogger(__name__)


def get_user(username: str) -> Optional[User]:
    logger.info(f'retrieving {username}')

    users = [i for i in db.collection(u'user').where(u'username', u'==', username).stream()]

    if len(users) == 0:
        logger.error(f'user {username} not found')
        return None
    if len(users) > 1:
        logger.critical(f"multiple {username}'s found")
        return None

    return parse_user(user_snapshot=users[0])


def parse_user(user_ref=None, user_snapshot=None) -> User:
    if user_ref is None and user_snapshot is None:
        raise ValueError('no user object supplied')

    if user_ref is None:
        user_ref = user_snapshot.reference

    if user_snapshot is None:
        user_snapshot = user_ref.get()

    user_dict = user_snapshot.to_dict()

    return User(username=user_dict.get('username'),
                password=user_dict.get('password'),
                db_ref=user_ref,

                user_type=User.Type[user_dict.get('type')])


def create_user(username: str,
                password: str,
                user_type: User.Type) -> None:
    logger.info(f'creating {username}')

    user_collection = db.collection(u'user')

    # check if username is already registered
    current_users = [i for i in user_collection.where(u'username', u'==', username).stream()]
    if len(current_users) > 0:
        logger.error(f'user {username} already exists')
        return None

    # USER DATABASE ENTITY MANIFEST
    user_info = {
        'username': username,
        'password': generate_password_hash(password),
        'type': user_type.name
    }

    user_collection.document().set(user_info)


def update_user(username: str, updates: dict):
    logger.info(f'updating {username}')

    user = get_user(username)

    if user is not None:
        user.db_ref.update(updates)
    else:
        logger.error('no user returned')


def delete_user(username: str) -> None:
    logger.info(f'deleting {username}')

    user = get_user(username)

    if user is not None:
        user.db_ref.delete()
    else:
        logger.error('no user returned')


def get_location(location_id: str) -> Optional[Location]:
    logger.info(f'retrieving {location_id}')

    locations = [i for i in db.collection(u'location').where(u'location_id', u'==', location_id).stream()]

    if len(locations) == 0:
        logger.error(f'location {location_id} not found')
        return None
    if len(locations) > 1:
        logger.critical(f"location {location_id}'s found")
        return None

    location = locations[0].to_dict()

    return Location(location_id=location.get('location_id'),
                    db_ref=locations[0].reference)


def create_location(location_id: str) -> None:
    logger.info(f'creating {location_id}')

    location_collection = db.collection(u'location')

    # check if location is already registered
    current_locations = [i for i in location_collection.where(u'location_id', u'==', location_id).stream()]
    if len(current_locations) > 0:
        logger.error(f'location {location_id} already exists')
        return None

    # LOCATION DATABASE ENTITY MANIFEST
    location_info = {
        'location_id': location_id
    }

    location_collection.document().set(location_info)


def update_location(location_id: str, updates: dict):
    logger.info(f'retrieving {location_id}')

    location = get_location(location_id)

    if location is not None:
        location.db_ref.update(updates)
    else:
        logger.error('no location returned')


def delete_location(location_id: str) -> None:
    logger.info(f'deleting {location_id}')

    location = get_location(location_id)

    if location is not None:
        location.db_ref.delete()
    else:
        logger.error('no location returned')
