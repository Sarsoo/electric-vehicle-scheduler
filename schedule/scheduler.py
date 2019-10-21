from flask import Flask, jsonify
import os

from .blueprint import auth_blueprint, location_blueprint, user_blueprint

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..', 'build'), template_folder="templates")

api_prefix = '/api'
app.register_blueprint(auth_blueprint, url_prefix=f'{api_prefix}/auth')
app.register_blueprint(location_blueprint, url_prefix=f'{api_prefix}/location')
app.register_blueprint(user_blueprint, url_prefix=f'{api_prefix}/user')


@app.route('/')
def root():
    return jsonify({
        'message': 'hello world'
    }), 200

# [END gae_python37_app]
