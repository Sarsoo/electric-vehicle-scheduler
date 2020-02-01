from google.cloud.firestore import DocumentReference
import schedule.db.database as db
from enum import Enum
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

import logging
import firebase_admin
import firebase_admin.messaging as messaging

logger = logging.getLogger(__name__)
fire_admin = firebase_admin.initialize_app()

restingScore = 500.0
ddtInactive = 0.00694444444  # +/-25 per hour, tends towards restingScore (500)
ddtIn_Queue = 2*ddtInactive  # +50 per hour
AssignedFixedPenalty = 450.0 
ddtConnected_Charging = 3*ddtInactive #-75 per hour
ddtConnected_Full = 6*ddtInactive     #-150 per hour

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
                 score_last_updated: datetime,

                 access_token: str,
                 access_token_last_refreshed: datetime,

                 notification_token: str):
        self.username = username
        self.db_ref = db_ref

        self._password = password
        self._type = user_type

        self._score = score
        self._state = state
        self._score_last_updated = score_last_updated

        self._access_token = access_token
        self._access_token_last_refreshed = access_token_last_refreshed

        self._notification_token = notification_token

    def to_dict(self) -> dict:
        return {
            'username': self.username,
            'type': self.user_type.name,
            'state': self.state.name
        }

    def __eq__(self, other):
        return isinstance(other, User) and other.username == self.username

    def __str__(self):
        return self.username

    def refresh_access_token(self):
        self.access_token = db.get_new_access_token()

    def send_notification(self, title: str, body: str):

        if self.notification_token is None:
            logger.error(f'{self.username} no notification token')
            return

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            android=messaging.AndroidConfig(
                priority='high'
            ),
            token=self.notification_token
        )

        response = messaging.send(message)
        logger.info(f'{response}')

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
        if self.state == value:
            return

        if self.state == self.State.inactive:
            if value == self.State.in_queue:
                pass
            elif value == self.State.assigned:
                self.send_notification('Scheduler', "You've been assigned a charger!")
            elif value in [self.State.connected_charging, self.State.connected_full]:
                logger.warning(f'weird state change, {self.state.name} to {value.name}')
        elif self.state == self.State.in_queue:
            if value == self.State.inactive:
                pass
            elif value == self.State.assigned:
                self.send_notification('Scheduler', "You've been assigned a charger!")
            elif value == self.State.connected_full:
                logger.warning(f'weird state change, {self.state.name} to {value.name}')
            elif value == self.State.connected_charging:
                self.send_notification('Scheduler', "Charging Started")
        elif self.state == self.State.assigned:
            if value == self.State.inactive:
                pass
            elif value in [self.State.in_queue, self.State.connected_full]:
                logger.warning(f'weird state change, {self.state.name} to {value.name}')
            elif value == self.State.connected_charging:
                pass
        elif self.state == self.State.connected_charging:
            if value == self.State.inactive:
                self.send_notification('Scheduler', "Session Cancelled")
            elif value in [self.State.in_queue, self.State.assigned]:
                logger.warning(f'weird state change, {self.state.name} to {value.name}')
            elif value == self.State.connected_full:
                self.send_notification('Scheduler', "INFO: Your car has finished charging, please move your car")
        elif self.state == self.State.connected_full:
            if value == self.State.inactive:
                pass
            elif value in [self.State.in_queue, self.State.assigned, self.State.connected_charging]:
                logger.warning(f'weird state change, {self.state.name} to {value.name}')

        db.update_user(self.username, {'state': value.name})
        self._state = value

    @property
    def score_last_updated(self):
        return self._score_last_updated

    @score_last_updated.setter
    def score_last_updated(self, value: datetime):
        db.update_user(self.username, {'score_last_updated': value})
        self._score_last_updated = value

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, value: float):
        db.update_user(self.username, {'access_token': value})
        self._access_token = value

    @property
    def notification_token(self):
        return self._notification_token

    @notification_token.setter
    def notification_token(self, value: float):
        db.update_user(self.username, {'notification_token': value})
        self._notification_token = value

    @property
    def access_token_last_refreshed(self):
        return self._access_token_last_refreshed

    @access_token_last_refreshed.setter
    def access_token_last_refreshed(self, value: float):
        db.update_user(self.username, {'access_token_last_refreshed': value})
        self._access_token_last_refreshed = value

    def update_score(self, time: datetime):
        self.score_last_updated = time
        time_diff = (time - self.score_last_updated).total_seconds()
        # INACTIVE - score tends towards Resting Score (default 500) at +/-25 per hour.
        if self.state == self.State.inactive:
            if self.score > restingScore:
                self.score = self.score - ddtInactive*time_diff
                if self.score < restingScore:
                    self.score = restingScore
            if self.score < restingScore:
                self.score = self.score + ddtInactive*time_diff
                if self.score > restingScore:
                    self.score = restingScore
        # IN_QUEUE - score increases at +50 per hour
        elif self.state == self.State.in_queue:
            self.score = self.score + ddtIn_Queue*time_diff
        # ASSIGNED - Score increases rapidly!
        # The AssignedFixedPenalty is implemented in function assignedFixedPenalty.
        elif self.state == self.State.assigned:
            self.score = self.score
        # CHARGING - score decreases at a rate of -75 per hour.
        elif self.state == self.State.connected_charging:
            self.score = self.score - ddtConnected_Charging*time_diff
            if self.score < 0:
                self.score = 0
        # FULL - score decreases at a rate of -150 per hour.
        elif self.state == self.State.connected_full:
            self.score = self.score - ddtConnected_Full*time_diff
