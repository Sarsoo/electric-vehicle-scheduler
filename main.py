from schedule import app
from schedule.util.auth_token_refresh import refresh_access_tokens
from schedule.util.reset_queue import reset_queue

app = app


def lambda_refresh_access_tokens(event, context):
    return refresh_access_tokens(event, context)


def lambda_reset_queue(event, context):
    return reset_queue(event, context)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
