from flask import Flask
from . import webcrawler


def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = 'hhhhhhssssssssssskkkkkkkk'

    app.register_blueprint(webcrawler.bp)

    return app
