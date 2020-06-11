import json
from argparse import ArgumentParser
from threading import Thread

from flask import Flask, jsonify
from flask import render_template, request, redirect
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String

from forms import EnvUpdateForm

AGP = ArgumentParser(prog='Web server for alerta', description='')
AGP.add_argument('--port', help='port to be listened', default=23456, type=int)
AGP.add_argument('--dbstring', help='Database connection string', type=str)
AGP.add_argument('--debug', help='debug mode', default=False, type=bool)
args, _ = AGP.parse_known_args()

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = args.dbstring
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


class Environments(db.Model):
    __tablename__ = 'alerta_environments'
    id = Column(Integer, primary_key=True)
    name = Column(String())

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<Topic {self.name}>"


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form['name'] != '':
            name = request.form['name']
            new_environment = Environments(name=name)
            try:
                db.session.add(new_environment)
                db.session.commit()
                return redirect('/')
            except Exception as Ex:
                return "There was a problem adding new record."
        else:
            return "Empty environment name."
    elif request.method == 'GET':
        env = Environments.query.order_by(Environments.id).all()
        return render_template('index.html', env=env)


@app.route('/env/delete/<int:id>')
def env_delete(id):
    environment = Environments.query.get_or_404(id)

    try:
        db.session.delete(environment)
        db.session.commit()
        return redirect('/')
    except:
        return "There was a problem deleting data."


@app.route('/env/update/<int:id>', methods=['GET', 'POST'])
def env_update(id):
    environment = Environments.query.filter_by(id=id).first_or_404()
    form = EnvUpdateForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        environment.name = form.name.data
        db.session.commit()
        return jsonify(status='ok')
    elif request.method == 'GET':
        form.name.data = environment.name
    else:
        data = json.dumps(form.errors, ensure_ascii=False)
        return jsonify(data)
    return render_template('/snippets/env_update.html', title="Edit environment", form=form)


def main():
    Thread(target=app.run, kwargs={'port': args.port, 'debug': args.debug}).start()


if __name__ == '__main__':
    main()
