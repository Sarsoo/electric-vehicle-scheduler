from google.cloud import firestore
import logging
import random, string
from datetime import datetime
from typing import Optional, List

from schedule.model.user import User
from schedule.model.location import Location, Charger
from schedule.model.session import Session

from werkzeug.security import generate_password_hash

db = firestore.Client()
logger = logging.getLogger(__name__)

illegal_characters = [' ', ':', '/']


def get_new_access_token():
    prospective_key = ''.join(random.choices(string.ascii_letters + string.digits, k=30))
    if prospective_key not in [i.access_token for i in get_users()]:
        return prospective_key
    else:
        return get_new_access_token()


def get_users():
    logger.debug('getting users')

    users = [i for i in db.collection(u'user').stream()]
    return [parse_user(user_snapshot=i) for i in users]


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

                user_type=User.Type[user_dict.get('type')],

                score=user_dict.get('score'),
                state=User.State[user_dict.get('state')],
                score_last_updated=user_dict.get('score_last_updated'),

                access_token=user_dict.get('access_token'),
                access_token_last_refreshed=user_dict.get('access_token_last_refreshed'))


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
        'type': user_type.name,
        'score': 500,
        'state': User.State.inactive.name,
        'score_last_updated': datetime.utcnow(),
        'access_token': get_new_access_token(),
        'access_token_last_refreshed': datetime.utcnow()
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
                    chargers=[parse_charger(charger_snapshot=i) for i in location_ref.collection('charger').stream()],
                    queue=[parse_user(user_ref=i) for i in location_dict.get('queue')])


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
        'location_id': location_id,
        'queue': []
    }

    location_collection.document().set(location_info)


def update_location(location_id: str, updates: dict):
    logger.debug(f'updating {location_id}')

    location = get_location(location_id)

    if location is not None:
        location.db_ref.update(updates)
    else:
        logger.error('no location returned')


def delete_location(location_id: str) -> None:
    logger.debug(f'deleting {location_id}')

    location = get_location(location_id)

    if location is not None:
        for charger in get_chargers(location_id):
            delete_charger(location_id, charger.charger_id)
        location.db_ref.delete()
    else:
        logger.error('no location returned')


def queue_user(location_id: str, user: User):
    logger.debug(f'queuing {user} at {location_id}')

    location = get_location(location_id)

    if location is not None:
        if user not in location.queue:
            location.queue = location.queue + [user]
            user.state = User.State.in_queue
            location.tick_queue()
        else:
            logger.error(f'{user} already queued at {location_id}')
            raise KeyError(f'{user} already queued at {location_id}')
    else:
        logger.error(f'{location_id} not found')
        raise FileNotFoundError(f'{location_id} not found')


def remove_user_from_queue(location_id: str, user: User):
    logger.debug(f'removing {user} from queue at {location_id}')

    location = get_location(location_id)

    if location is not None:
        if user in location.queue:
            new_queue = location.queue
            new_queue.remove(user)
            location.queue = new_queue

            user.state = User.State.inactive
        else:
            logger.error(f'{user} not queued at {location_id}')
            raise KeyError(f'{user} not queued at {location_id}')
    else:
        logger.error(f'{location_id} not found')
        raise FileNotFoundError(f'{location_id} not found')


def get_chargers(location_id: str) -> Optional[List[Charger]]:

    location = get_location(location_id)
    return [parse_charger(charger_snapshot=i) for i in location.db_ref.collection(u'charger').stream()]


def get_charger(location_id: str, charger_id: str) -> Optional[Charger]:
    logger.debug(f'retrieving {location_id}:{charger_id}')

    location = get_location(location_id)

    if location is None:
        logger.error(f'location {location_id} not found')
        return None

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

    return Charger(location_id=charger_dict.get('location_id'),
                   charger_id=charger_dict.get('charger_id'),
                   db_ref=charger_ref,
                   active_session=charger_dict.get('active_session'),
                   state=Charger.State[charger_dict.get('state')])


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
            'location_id': location_id,
            'charger_id': charger_id,
            'active_session': None,
            'state': Charger.State.available.name
        }

        charger_collection.document().set(charger_info)

    else:
        logger.error(f'location {location_id} not found')
        return None


def update_charger(location_id: str, charger_id: str, updates: dict):
    logger.debug(f'updating {location_id}:{charger_id}')

    charger = get_charger(location_id, charger_id)

    if charger is not None:
        charger.db_ref.update(updates)
    else:
        logger.error(f'{location_id}:{charger_id} not returned')


def delete_charger(location_id: str, charger_id: str) -> None:
    logger.debug(f'deleting {location_id}:{charger_id}')

    charger = get_charger(location_id, charger_id)

    if charger is not None:
        for session in get_sessions(location_id, charger_id):
            session.db_ref.delete()
        charger.db_ref.delete()
    else:
        logger.error(f'{location_id}:{charger_id} not returned')


def get_sessions(location_id: str, charger_id: str):
    logger.debug(f'retrieving sessions for {location_id}:{charger_id}')

    charger = get_charger(location_id, charger_id)
    if charger is None:
        logger.error(f'charger {location_id}:{charger_id} not found')
        return None

    sessions = [i for i in charger.db_ref.collection(u'session').stream()]

    return [parse_session(session_snapshot=i) for i in sessions]


def get_session(location_id: str, charger_id: str, session_id: int):
    logger.debug(f'retrieving {location_id}:{charger_id}:{session_id}')

    charger = get_charger(location_id, charger_id)
    if charger is None:
        logger.error(f'charger {location_id}:{charger_id} not found')
        return None

    sessions = [i for i in charger.db_ref.collection(u'session').where(u'session_id', u'==', session_id).stream()]

    if len(sessions) == 0:
        logger.error(f'session {location_id}:{charger_id}:{session_id} not found')
        return None

    if len(sessions) > 1:
        logger.critical(f"multiple {location_id}:{charger_id}:{session_id}'s found")
        return None

    return parse_session(session_snapshot=sessions[0])


def get_active_session(location_id: str, charger_id: str) -> Optional[Session]:

    logger.debug(f'retrieving active session for {location_id}:{charger_id}')

    charger = get_charger(location_id, charger_id)
    if charger is None:
        logger.error(f'charger {location_id}:{charger_id} not found')
        return None

    if charger.active_session is None:
        logger.debug(f'no active session for {location_id}:{charger_id}')
        return None

    sessions = [i for i in get_sessions(location_id, charger_id) if i.session_id == charger.active_session]

    if len(sessions) == 0:
        logger.error(f'active session not found for {location_id}:{charger_id}')
        return None

    if len(sessions) > 1:
        logger.critical(f'multiple active sessions found for {location_id}:{charger_id}')
        return None

    return sessions[0]


def start_session(location_id: str, charger_id: str, user: User):

    logger.debug(f'starting session for {location_id}:{charger_id}')

    charger = get_charger(location_id, charger_id)
    if charger is None:
        logger.error(f'charger {location_id}:{charger_id} not found')
        raise FileNotFoundError('charger not found')

    if charger.active_session is not None:
        logger.error(f'session already running on {location_id}:{charger_id}')
        raise FileExistsError('session already running')

    session_id = get_new_session_id(location_id, charger_id)

    charger.db_ref.collection('session').document().set({
        'location_id': location_id,
        'charger_id': charger_id,
        'session_id': session_id,
        'start_time': datetime.utcnow(),
        'end_time': None,
        'user': user.db_ref
    })
    charger.active_session = session_id
    charger.state = Charger.State.pre_session
    remove_user_from_queue(location_id, user)


def get_new_session_id(location_id: str, charger_id: str):
    sessions = get_sessions(location_id, charger_id)

    if sessions is None:
        return None

    if len(sessions) == 0:
        return 1

    max_value = max([i.session_id for i in sessions])

    session_id = max_value + 1
    while session_id in [i.session_id for i in sessions]:
        session_id = session_id + 1

    return session_id


def parse_session(session_ref=None, session_snapshot=None) -> Session:
    if session_ref is None and session_snapshot is None:
        raise ValueError('no charger object supplied')

    if session_ref is None:
        session_ref = session_snapshot.reference

    if session_snapshot is None:
        session_snapshot = session_ref.get()

    charger_dict = session_snapshot.to_dict()

    return Session(location_id=charger_dict.get('location_id'),
                   charger_id=charger_dict.get('charger_id'),
                   session_id=charger_dict.get('session_id'),
                   db_ref=session_ref,
                   start_time=charger_dict.get('start_time'),
                   end_time=charger_dict.get('end_time'),
                   user=parse_user(charger_dict.get('user')))


def update_session(location_id: str, charger_id: str, updates: dict):
    logger.debug(f'updating {location_id}:{charger_id} session')

    session = get_active_session(location_id, charger_id)

    if session is not None:
        session.db_ref.update(updates)
    else:
        logger.error(f'{location_id}:{charger_id} session not returned')


def end_session(location_id: str, charger_id: str):
    logger.debug(f'stopping {location_id}:{charger_id} session')

    session = get_active_session(location_id, charger_id)

    if session is not None:
        session.end_time = datetime.utcnow()
        charger = get_charger(location_id, charger_id)
        charger.state = Charger.State.available
        charger.active_session = None
        get_location(location_id).tick_queue()
    else:
        logger.error(f'no active session at {location_id}:{charger_id}')
        raise FileNotFoundError('no session found')


def delete_session(location_id: str, charger_id: str, session_id):
    logger.debug(f'deleting {location_id}:{charger_id} session')

    session = get_session(location_id, charger_id, session_id)

    if session is not None:
        session.db_ref.delete()
    else:
        logger.error(f'session {location_id}:{charger_id}:{session_id} not found')
        raise FileNotFoundError('session not found')
