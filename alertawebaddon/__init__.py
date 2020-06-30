import os
from argparse import ArgumentParser

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

AGP = ArgumentParser(prog='Web server for alerta', description='')
AGP.add_argument('--port', help='port to be listened', default=23456, type=int)
AGP.add_argument('--dbstring', help='Database connection string', type=str)
AGP.add_argument('--debug', help='debug mode', default=False, type=bool)
AGP.add_argument('--ldap_domain', help='debug mode', default=False, type=str)
args, _ = AGP.parse_known_args()

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = args.dbstring
app.config['WTF_CSRF_SECRET_KEY'] = 'csrf'
app.config['GITHUB_OAUTH_CLIENT_ID'] = os.environ.get("GITHUB_OAUTH_CLIENT_ID")
app.config['GITHUB_OAUTH_CLIENT_SECRET'] = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET")
app.secret_key = os.environ.get("APP_SECRET_KEY")

db = SQLAlchemy(app)
db.create_all()
