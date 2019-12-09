from google.cloud.firestore import DocumentReference
import schedule.db.database as db
from enum import Enum
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

restingScore = 500.0
ddtInactive = 0.00694444444  # +/-25 per hour, tends towards restingScore (500)
ddtIn_Queue = -ddtInactive
ddtAssigned = -10*ddtInactive
ddtConnected_Charging = ddtInactive
ddtConnected_Full = ddtInactive


class User:
    class Type(Enum):
        user = 1
        admin = 2
        service = 3

    class State(Enum):
        inactive = 1  # Not in a Queue or connected to a charger.
        in_queue = 2  # In a queue waiting for a charger.
        assigned = 3  # In a queue, assigned a charger, waiting to move the car.
        connected_charging = 4  # Connected to a charger and charging.
        connected_full = 5  # Connected to a charger, charge finished.

    def __init__(self,
                 username: str,
                 db_ref: DocumentReference,

                 password: str,
                 user_type: Type,

                 score: float,
                 state: State,
                 score_last_updated: datetime):
        self.username = username
        self.db_ref = db_ref

        self._password = password
        self._type = user_type

        self._score = score
        self._state = state
        self._score_last_updated = score_last_updated

    def to_dict(self) -> dict:
        return {
            'username': self.username,
            'type': self.user_type.name,
            'state': self.state.name
        }

    def __eq__(self, other):
        return isinstance(other, User) and other.username == self.username

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

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value: float):
        db.update_user(self.username, {'score': value})
        self._score = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: State):
        db.update_user(self.username, {'state': value.name})
        self._state = value

    @property
    def score_last_updated(self):
        return self._score_last_updated

    @score_last_updated.setter
    def score_last_updated(self, value: float):
        db.update_user(self.username, {'score_last_updated': value})
        self._score_last_updated = value

    def update_score(self, time):
        time_diff = (time - self.score_last_updated).total_seconds()
        # INACTIVE - score tends towards Resting Score
        if self.state == self.State.inactive:
            if self.score > restingScore:
                self.score = self.score - ddtInactive*time_diff
                if self.score < restingScore:
                    self.score = restingScore
            if self.score < restingScore:
                self.score = self.score + ddtInactive*time_diff
                if self.score > restingScore:
                    self.score = restingScore
        # IN_QUEUE - score tends towards 0
        elif self.state == self.State.in_queue:
            self.score = self.score + ddtIn_Queue*time_diff
        if self.score < 0:
            self.score = 0
        # ASSIGNED - Score increases rapidly!
        # Think about implementing a timeout - ie user moves to Inactive if they don't plug in after say one hour.
        # Timeout time should be parameterized, specific to each location.
        elif self.state == self.State.assigned:
            self.score = self.score + ddtAssigned*time_diff
        # CHARGING - score tends towards Resting Score.
        elif self.state == self.State.connected_charging:
            if self.score > restingScore:
                self.score = self.score - ddtConnected_Charging*time_diff
                if self.score < restingScore:
                    self.score = restingScore
        if self.score < restingScore:
            self.score = self.score + ddtConnected_Charging*time_diff
            if self.score > restingScore:
                self.score = restingScore
        # FULL - Score increases rapidly!
        # Penalises those who let their car stay connected for long periods of time.
        # Think about implementing an offset to only start increasing score after a certain amount of time.
        elif self.state == self.State.connected_full:
            self.score = self.score + ddtConnected_Full*time_diff

    def make_inactive(self):
        self.update_score()
        self.state = self.State.inactive
        # BODY

    def add_to_queue(self):
        self.update_score()
        self.state = self.State.in_queue
        # BODY

    def assign_to_charger(self):
        self.update_score()
        self.state = self.State.assigned
        # BODY

    def set_charging(self):
        self.update_score()
        self.state = self.State.connected_charging
        # BODY

    def set_full(self):
        self.update_score()
        self.state = self.State.connected_full
        # BODY
