from google.cloud.firestore import DocumentReference
from typing import List
from enum import Enum
from datetime import datetime

import schedule.db.database as database
from schedule.model.user import User
from schedule.model.session import Session
import logging

logger = logging.getLogger(__name__)


class Charger:

    class State(Enum):
        available = 1
        pre_session = 2
        charging = 3
        full = 4

    def __init__(self,
                 location_id: str,
                 charger_id: str,
                 db_ref: DocumentReference,

                 state: State,
                 active_session: int = None,
                 active_session_obj: Session = None):

        self.location_id = location_id
        self.charger_id = charger_id
        self.db_ref = db_ref

        if active_session_obj is not None:
            active_session = active_session_obj.session_id

        self._active_session_obj = active_session_obj
        self._active_session = active_session
        self._state = state

    def to_dict(self) -> dict:
        return {
            'location_id': self.location_id,
            'charger_id': self.charger_id,
            'active_session': self.active_session,
            # 'session': self.active_session_obj.to_dict() if self.active_session_obj is not None else None,
            'state': self.state.name
        }

    def __str__(self):
        return f'{self.location_id}:{self.charger_id}'

    @property
    def active_session(self) -> int:
        return self._active_session

    @active_session.setter
    def active_session(self, value: int):
        database.update_charger(self.location_id, self.charger_id, {'active_session': value})
        self._active_session = value
        self.active_session_obj = database.get_session(self.location_id, self.charger_id, self.active_session)

    @property
    def active_session_obj(self) -> Session:
        return self._active_session_obj

    @active_session_obj.setter
    def active_session_obj(self, value: Session):
        self._active_session = value.session_id if value is not None else None
        self._active_session_obj = value

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, value: State):
        if self.active_session is not None and self.active_session_obj is None:
            self.active_session_obj = database.get_active_session(self.location_id, self.charger_id)
        self._update_state(value)
        database.update_charger(self.location_id, self.charger_id, {'state': value.name})
        self._state = value

    def _update_state(self, new_state: State):
        if self.state == new_state:
            return

        if self.state == self.State.available:
            if new_state == self.State.pre_session:
                self.active_session_obj.user.state = User.State.assigned
            else:
                raise SystemError(f'Cannot move from {self.state.name} to {new_state.name}')
        elif self.state == self.State.pre_session:
            if new_state == self.State.charging:
                self.active_session_obj.user.state = User.State.connected_charging
            elif new_state == self.State.available:
                self.active_session_obj.user.state = User.State.inactive
            else:
                raise SystemError(f'Cannot move from {self.state.name} to {new_state.name}')
        elif self.state == self.State.charging:
            if new_state == self.State.available:
                self.active_session_obj.user.state = User.State.inactive
            elif new_state == self.State.full:
                self.active_session_obj.user.state = User.State.connected_full
            else:
                raise SystemError(f'Cannot move from {self.state.name} to {new_state.name}')
        elif self.state == self.State.full:
            if new_state == self.State.available:
                self.active_session_obj.user.state = User.State.inactive
            elif new_state == self.State.charging:
                logger.warning(f'weird state change from {self.state} to {new_state}')
                self.active_session_obj.user.state = User.State.connected_charging
            else:
                raise SystemError(f'Cannot move from {self.state.name} to {new_state.name}')


class Location:
    def __init__(self,
                 location_id: str,
                 db_ref: DocumentReference,

                 chargers: List[Charger],
                 queue: List[User]):
        self.location_id = location_id
        self.db_ref = db_ref

        self.chargers = chargers

        self._queue = queue

    def __str__(self):
        return self.location_id

    def add_charger(self, charger_id: str):
        database.create_charger(self.location_id, charger_id)
        self.chargers = database.get_chargers(self.location_id)

    def to_dict(self) -> dict:
        return {
            'location_id': self.location_id,
            'chargers': [i.to_dict() for i in self.chargers],
            'queue': [i.to_dict() for i in self.queue]
        }

    @property
    def queue(self) -> List[User]:
        return self._queue

    @queue.setter
    def queue(self, value: List[User]):
        self.tick_queue()
        database.update_location(self.location_id, {'queue': [i.db_ref for i in value]})
        self._queue = value

    def tick_queue(self):
        if len(self.queue) == 0:
            return

        time = datetime.now()
        for user in self.queue:
            user.update_score(time)

        inactive_chargers = [i for i in self.chargers if i.active_session is None]

        if len(inactive_chargers) > 0:
            queue = sorted(self.queue.copy(), key=lambda x: x.score)
            users = queue[:len(inactive_chargers)]

            for user, charger in zip(users, inactive_chargers):
                database.start_session(self.location_id, charger.charger_id, user)
