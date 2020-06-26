from argparse import ArgumentParser

from flask import Flask
from flask_login import LoginManager
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
app.config['LDAP_PROVIDER_URL'] = 'ldap://ldap.testathon.net:389/'
app.config['LDAP_PROTOCOL_VERSION'] = 3

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)
db.create_all()
