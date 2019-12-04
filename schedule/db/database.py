from google.cloud import firestore
import logging
from typing import Optional, List

from schedule.model.user import User
from schedule.model.location import Location, Charger

from werkzeug.security import generate_password_hash

db = firestore.Client()
logger = logging.getLogger(__name__)

illegal_characters = [' ', ':']


def get_user(username: str) -> Optional[User]:
    logger.debug(f'retrieving {username}')

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

    logger.debug(f'creating {username}')

    user_collection = db.collection(u'user')

    # check if username is already registered
    current_users = [i for i in user_collection.where(u'username', u'==', username).stream()]
    if len(current_users) > 0:
        logger.error(f'user {username} already exists')
        raise FileExistsError('user already registered')

    # USER DATABASE ENTITY MANIFEST
    user_info = {
        'username': username,
        'password': generate_password_hash(password),
        'type': user_type.name
    }

    user_collection.document().set(user_info)


def update_user(username: str, updates: dict):
    logger.debug(f'updating {username}')

    user = get_user(username)

    if user is not None:
        user.db_ref.update(updates)
    else:
        logger.error('no user returned')


def delete_user(username: str) -> None:
    logger.debug(f'deleting {username}')

    user = get_user(username)

    if user is not None:
        user.db_ref.delete()
    else:
        logger.error('no user returned')


def get_locations() -> Optional[List[Location]]:
    logger.debug('retrieving all locations')

    locations = [i for i in db.collection(u'location').stream()]
    return [parse_location(location_snapshot=i) for i in locations]


def get_location(location_id: str) -> Optional[Location]:
    logger.debug(f'retrieving {location_id}')

    locations = [i for i in db.collection(u'location').where(u'location_id', u'==', location_id).stream()]

    if len(locations) == 0:
        logger.error(f'location {location_id} not found')
        return None
    if len(locations) > 1:
        logger.critical(f"location {location_id}'s found")
        return None

    return parse_location(location_snapshot=locations[0])


def parse_location(location_ref=None, location_snapshot=None) -> Location:
    if location_ref is None and location_snapshot is None:
        raise ValueError('no location object supplied')

    if location_ref is None:
        location_ref = location_snapshot.reference

    if location_snapshot is None:
        location_snapshot = location_ref.get()

    location_dict = location_snapshot.to_dict()

    return Location(location_id=location_dict.get('location_id'),
                    db_ref=location_ref,
                    chargers=[parse_charger(charger_snapshot=i) for i in location_ref.collection('charger').stream()])


def create_location(location_id: str) -> None:

    for char in illegal_characters:
        if char in location_id:
            raise ValueError(f'illegal char "{char}" present in location id')

    logger.debug(f'creating {location_id}')

    location_collection = db.collection(u'location')

    # check if location is already registered
    current_locations = [i for i in location_collection.where(u'location_id', u'==', location_id).stream()]
    if len(current_locations) > 0:
        logger.error(f'location {location_id} already exists')
        raise FileExistsError('location already registered')

    # LOCATION DATABASE ENTITY MANIFEST
    location_info = {
        'location_id': location_id
    }

    location_collection.document().set(location_info)


def update_location(location_id: str, updates: dict):
    logger.debug(f'retrieving {location_id}')

    location = get_location(location_id)

    if location is not None:
        location.db_ref.update(updates)
    else:
        logger.error('no location returned')


def delete_location(location_id: str) -> None:
    logger.debug(f'deleting {location_id}')

    location = get_location(location_id)

    if location is not None:
        location.db_ref.delete()
    else:
        logger.error('no location returned')


def get_chargers(location_id: str) -> Optional[List[Charger]]:

    location = get_location(location_id)
    return [parse_charger(charger_snapshot=i) for i in location.db_ref.collection(u'charger').stream()]


def get_charger(location_id: str, charger_id: str) -> Optional[Charger]:
    logger.debug(f'retrieving {location_id}:{charger_id}')

    location = get_location(location_id)

    chargers = [i for i in location.db_ref.collection(u'charger').where(u'charger_id', u'==', charger_id).stream()]

    if len(chargers) == 0:
        logger.error(f'charger {location_id}:{charger_id} not found')
        return None
    if len(chargers) > 1:
        logger.critical(f"{len(chargers)} {location_id}:{charger_id}'s found")
        return None

    return parse_charger(charger_snapshot=chargers[0])


def parse_charger(charger_ref=None, charger_snapshot=None) -> Charger:
    if charger_ref is None and charger_snapshot is None:
        raise ValueError('no charger object supplied')

    if charger_ref is None:
        charger_ref = charger_snapshot.reference

    if charger_snapshot is None:
        charger_snapshot = charger_ref.get()

    charger_dict = charger_snapshot.to_dict()

    return Charger(charger_id=charger_dict.get('charger_id'),
                   db_ref=charger_ref)


def create_charger(location_id: str, charger_id: str) -> None:

    for char in illegal_characters:
        if char in charger_id:
            raise ValueError(f'illegal char "{char}" present in charger id')

    logger.debug(f'creating {location_id}:{charger_id}')

    location = get_location(location_id)

    if location is not None:

        charger_collection = location.db_ref.collection(u'charger')

        # check if charger is already registered
        charger_stream = [i for i in charger_collection.where(u'charger_id', u'==', charger_id).stream()]
        if len(charger_stream) > 0:
            logger.error(f'charger {charger_id} already exists')
            raise FileExistsError('charger already registered')

        # CHARGER DATABASE ENTITY MANIFEST
        charger_info = {
            'charger_id': charger_id
        }

        charger_collection.document().set(charger_info)

    else:
        logger.error(f'location {location_id} not found')
        return None


def update_charger(location_id: str, charger_id: str, updates: dict):
    logger.debug(f'retrieving {location_id}:{charger_id}')

    charger = get_charger(location_id, charger_id)

    if charger is not None:
        charger.db_ref.update(updates)
    else:
        logger.error(f'{location_id}:{charger_id} not returned')


def delete_charger(location_id: str, charger_id: str) -> None:
    logger.debug(f'deleting {location_id}:{charger_id}')

    charger = get_charger(location_id, charger_id)

    if charger is not None:
        charger.db_ref.delete()
    else:
        logger.error(f'{location_id}:{charger_id} not returned')
