import os
from argparse import ArgumentParser

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

AGP = ArgumentParser(prog='Web server for alerta', description='')
AGP.add_argument('--port', help='port to be listened', default=23456, type=int)
AGP.add_argument('--debug', help='debug mode', default=False, type=bool)
args, _ = AGP.parse_known_args()

MANDATORY_ENV_VARS = ["DATABASE_URL",
                      "GITHUB_OAUTH_CLIENT_ID",
                      "GITHUB_OAUTH_CLIENT_SECRET",
                      "GITHUB_OAUTH_ALLOWED_ORGANIZATIONS",
                      "APP_SECRET_KEY"]

for var in MANDATORY_ENV_VARS:
    if var not in os.environ:
        raise EnvironmentError("Failed because {} is not set.".format(var))

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['GITHUB_OAUTH_CLIENT_ID'] = os.environ.get("GITHUB_OAUTH_CLIENT_ID")
app.config['GITHUB_OAUTH_CLIENT_SECRET'] = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET")
app.config['GITHUB_OAUTH_ALLOWED_ORGANIZATIONS'] = \
    os.environ.get("GITHUB_OAUTH_ALLOWED_ORGANIZATIONS", default="opentelekomcloud-infra")
app.secret_key = os.environ.get("APP_SECRET_KEY")
app.config['WTF_CSRF_SECRET_KEY'] = 'csrf'

db = SQLAlchemy(app)
