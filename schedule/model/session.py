from datetime import datetime
from google.cloud.firestore import DocumentReference

import schedule.db.database as database
from schedule.model.user import User


class Session:
    def __init__(self,
                 location_id: str,
                 charger_id: str,
                 session_id: int,
                 start_time: datetime,
                 end_time: datetime,
                 user: User,

                 db_ref: DocumentReference):
        self.location_id = location_id
        self.charger_id = charger_id
        self.session_id = session_id

        self._start_time = start_time
        self._end_time = end_time
        self._user = user

        self.db_ref = db_ref

    def to_dict(self) -> dict:
        return {
            'location_id': self.location_id,
            'charger_id': self.charger_id,
            'session_id': self.session_id,

            'start_time': self.start_time,
            'end_time': self.end_time,
            'user': self.user.to_dict()
        }

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, value: datetime):
        database.update_session(self.location_id, self.charger_id, {'start_time': value})
        self._start_time = value

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, value: datetime):
        database.update_session(self.location_id, self.charger_id, {'end_time': value})
        self._end_time = value

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value: User):
        database.update_session(self.location_id, self.charger_id, {'user': value})
        self._user = value
