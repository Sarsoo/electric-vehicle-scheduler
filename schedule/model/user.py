from google.cloud.firestore import DocumentReference


class User:
    def __init__(self,
                 username: str,
                 db_ref: DocumentReference):
        self.username = username
        self.db_ref = db_ref

    def to_dict(self) -> dict:
        return {
            'username': self.username
        }
