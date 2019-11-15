from google.cloud.firestore import DocumentReference
from typing import List


class Charger:
    def __init__(self,
                 location_id: str,
                 db_ref: DocumentReference):
        self.charger_id = location_id
        self.db_ref = db_ref

    def to_dict(self) -> dict:
        return {
            'charger_id': self.charger_id
        }


class Location:
    def __init__(self,
                 location_id: str,
                 db_ref: DocumentReference,

                 chargers: List[Charger]):
        self.location_id = location_id
        self.db_ref = db_ref

        self.chargers = chargers

    def to_dict(self) -> dict:
        return {
            'location_id': self.location_id
        }
