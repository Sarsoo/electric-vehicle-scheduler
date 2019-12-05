from google.cloud.firestore import DocumentReference
from typing import List
from enum import Enum

import schedule.db.database as database
from schedule.model.user import User


class Charger:

    class State(Enum):
        Charging = 1
        Full = 2
        Available = 3

    def __init__(self,
                 location_id: str,
                 charger_id: str,
                 db_ref: DocumentReference,

                 active_session: int,
                 state: State):

        self.location_id = location_id
        self.charger_id = charger_id
        self.db_ref = db_ref

        self._active_session = active_session
        self._state = state

    def to_dict(self) -> dict:
        return {
            'location_id': self.location_id,
            'charger_id': self.charger_id,
            'active_session': self.active_session,
            'state': self.state.name
        }

    @property
    def active_session(self) -> int:
        return self._active_session

    @active_session.setter
    def active_session(self, value: int):
        database.update_charger(self.location_id, self.charger_id, {'active_session': value})
        self._active_session = value

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, value: State):
        database.update_charger(self.location_id, self.charger_id, {'state': value.name})
        self._state = value


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
        database.update_location(self.location_id, {'queue': [i.db_ref for i in value]})
        self._queue = value

    def tick_queue(self):
        pass
