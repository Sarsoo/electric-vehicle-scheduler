from google.cloud.firestore import DocumentReference
from typing import List

import schedule.db.database as database


class Charger:
    def __init__(self,
                 location_id: str,
                 charger_id: str,
                 db_ref: DocumentReference,

                 active_session: int):

        self.location_id = location_id
        self.charger_id = charger_id
        self.db_ref = db_ref

        self._active_session = active_session

    def to_dict(self) -> dict:
        return {
            'location_id': self.location_id,
            'charger_id': self.charger_id,
            'active_session': self.active_session
        }

    @property
    def active_session(self) -> int:
        return self._active_session

    @active_session.setter
    def active_session(self, value: int):
        database.update_charger(self.location_id, self.charger_id, {'active_session': value})
        self._active_session = value


class Location:
    def __init__(self,
                 location_id: str,
                 db_ref: DocumentReference,

                 chargers: List[Charger]):
        self.location_id = location_id
        self.db_ref = db_ref

        self.chargers = chargers

    def add_charger(self, charger_id: str):
        database.create_charger(self.location_id, charger_id)
        self.chargers = database.get_chargers(self.location_id)

    def to_dict(self) -> dict:
        return {
            'location_id': self.location_id,
            'chargers': [i.to_dict() for i in self.chargers]
        }
