from google.cloud.firestore import DocumentReference
import schedule.db.database as db
from enum import Enum
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

restingScore = 500.0
ddtInactive = 0.00694444444 #+/-25 per hour, tends towards restingScore (500)
ddtIn_Queue = -ddtInactive
ddtAssigned = -10*ddtInactive
ddtConnected_Charging = ddtInactive
ddtConnected_Full = ddtInactive


class User:
    class Type(Enum):
        user = 1
        admin = 2
        service = 3

    class UserState(Enum):
        Inactive = 1  # Not in a Queue or connected to a charger.
        In_Queue = 2  # In a queue waiting for a charger.
        Assigned = 3  # In a queue, assigned a charger, waiting to move the car.
        Connected_Charging = 4  # Connected to a charger and charging.
        Connected_Full = 5  # Connected to a charger, charge finished.

    def __init__(self,
                 username: str,
                 db_ref: DocumentReference,

                 password: str,
                 user_type: Type,

                 score: float,
                 user_state: UserState,
                 score_last_updated: datetime):
        self.username = username
        self.db_ref = db_ref

        self._password = password
        self._type = user_type

        self._score = score
        self._user_state = user_state
        self._score_last_updated = score_last_updated

    def to_dict(self) -> dict:
        return {
            'username': self.username,
            'type': self.user_type.name,
            'user_state': self.user_state.name
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
    def user_state(self):
        return self._user_state

    @user_state.setter
    def user_state(self, value: UserState):
        db.update_user(self.username, {'user_state': value.name})
        self._user_state = value

    @property
    def score_last_updated(self):
        return self._score_last_updated

    @score_last_updated.setter
    def score_last_updated(self, value: float):
        db.update_user(self.username, {'score_last_updated': value})
        self._score_last_updated = value

    def update_score(self, time):
        time_diff = (time - self.score_last_updated).total_seconds()
        #INACTIVE - score tends towards Resting Score
        if self.user_state == self.UserState.Inactive:
            if self.score > restingScore:
                self.score = self.score - ddtInactive*time_diff
                if self.score < restingScore:
                    self.score = restingScore
            if self.score < restingScore:
                self.score = self.score + ddtInactive*time_diff
                if self.score > restingScore:
                    self.score = restingScore
        #IN_QUEUE - score tends towards 0
        elif self.user_state == self.UserState.In_Queue:
            self.score = self.score + ddtIn_Queue*time_diff
        if self.score < 0:
            self.score = 0
        #ASSIGNED - Score increases rapidly!
        #Think about implementing a timeout - ie user moves to Inactive if they don't plug in after say one hour.
        #Timeout time should be parameterized, specific to each location.
        elif self.user_state == self.UserState.Assigned:
            self.score = self.score + ddtAssigned*time_diff
        #CHARGING - score tends towards Resting Score.
        elif self.user_state == self.UserState.Connected_Charging:
            if self.score > restingScore:
                self.score = self.score - ddtConnected_Charging*time_diff
                if self.score < restingScore:
                    self.score = restingScore
        if self.score < restingScore:
            self.score = self.score + ddtConnected_Charging*time_diff
            if self.score > restingScore:
                self.score = restingScore
        #FULL - Score increases rapidly!
        #Penalises those who let their car stay connected for long periods of time.
        #Think about implementing an offset to only start increasing score after a certain amount of time.
        elif self.user_state == self.UserState.Connected_Full:
            self.score = self.score + ddtConnected_Full*time_diff

    def makeInactive(self):
        self.update_score()
        self.user_state = self.UserState.Inactive
        # BODY

    def addToQueue(self):
        self.update_score()
        self.user_state = self.UserState.In_Queue
        # BODY

    def assignToCharger(self):
        self.update_score()
        self.user_state = self.UserState.Assigned
        # BODY

    def setToCharging(self):
        self.update_score()
        self.user_state = self.UserState.Connected_Charging
        # BODY

    def setToFull(self):
        self.update_score()
        self.user_state = self.UserState.Connected_Full
        # BODY