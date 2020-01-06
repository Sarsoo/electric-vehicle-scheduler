import schedule.db.database as database
import logging

logger = logging.getLogger(__name__)


def reset_queue(event, context):
    locations = database.get_locations()
    for location in [i for i in locations if i.reset_queue_daily]:

        for user in location.queue:
            database.remove_user_from_queue(location_id=location.location_id, user=user)

        location.queue = []

    return 'ok'
