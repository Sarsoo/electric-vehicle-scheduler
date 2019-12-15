from schedule.model.user import User
import schedule.db.database as database
import logging

logger = logging.getLogger(__name__)


def refresh_access_tokens(event, context):
    users = database.get_users()
    for user in [i for i in users if i.user_type != User.Type.service]:
        user.refresh_access_token()

    return 'ok'
