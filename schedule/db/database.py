from google.cloud import firestore
import logging
from typing import Optional

from schedule.model.user import User
from schedule.model.location import Location

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

    user = users[0].to_dict()

    return User(username=user.get('username'))


def create_user(username: str) -> None:
    logger.info(f'creating {username}')

    user_collection = db.collection(u'user')

    # check if username is already registered
    current_users = [i for i in user_collection.where(u'username', u'==', username).stream()]
    if len(current_users) > 0:
        logger.error(f'user {username} already exists')
        return None

    # USER DATABASE ENTITY MANIFEST
    user_info = {
        'username': username
    }

    user_collection.document().set(user_info)


def update_user(username: str):
    pass


def delete_user(username: str) -> None:
    logger.info(f'deleting {username}')

    users = [i for i in db.collection(u'user').where(u'username', u'==', username).stream()]

    if len(users) == 0:
        logger.error(f'user {username} not found')
        return None
    if len(users) > 1:
        logger.critical(f"multiple {username}'s found")
        return None

    users[0].reference.delete()


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

    return Location(location_id=location.get('location_id'))


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


def update_location(username: str):
    pass


def delete_location(location_id: str) -> None:
    logger.info(f'deleting {location_id}')

    locations = [i for i in db.collection(u'location').where(u'location_id', u'==', location_id).stream()]

    if len(locations) == 0:
        logger.error(f'location {location_id} not found')
        return None
    if len(locations) > 1:
        logger.critical(f"multiple {location_id}'s found")
        return None

    locations[0].reference.delete()
