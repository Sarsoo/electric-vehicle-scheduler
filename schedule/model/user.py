from google.cloud.firestore import DocumentReference
import schedule.db.database as db
from enum import Enum

from werkzeug.security import generate_password_hash, check_password_hash


class User:
    class Type(Enum):
        user = 1
        admin = 2
        service = 3

    def __init__(self,
                 username: str,
                 db_ref: DocumentReference,

                 password: str,
                 user_type: Type):
        self.username = username
        self.db_ref = db_ref

        self._password = password
        self._type = user_type

    def to_dict(self) -> dict:
        return {
            'username': self.username,
            'type': self.user_type.name
        }

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, val: str):
        pw_hash = generate_password_hash(val)
        db.update_user(self.username, {'password': pw_hash})
        self._password = pw_hash

    def check_password(self, value: str) -> bool:
        return check_password_hash(self.password, value)

    @property
    def user_type(self):
        return self._type

    @user_type.setter
    def user_type(self, value: Type):
        db.update_user(self.username, {'type': value.name})
        self._type = value
