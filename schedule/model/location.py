from google.cloud.firestore import DocumentReference


class Location:
    def __init__(self,
                 location_id: str,
                 db_ref: DocumentReference):
        self.location_id = location_id
        self.db_ref = db_ref

    def to_dict(self) -> dict:
        return {
            'location_id': self.location_id
        }
