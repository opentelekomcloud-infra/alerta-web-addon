import json
from argparse import ArgumentParser
from threading import Thread

from flask import Flask, jsonify
from flask import render_template, request, redirect
from flask_bootstrap import Bootstrap
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from forms import EnvUpdateForm
from model import Environments, Topics, Templates, TopicsToSkip

AGP = ArgumentParser(prog='Web server for alerta', description='')
AGP.add_argument('--port', help='port to be listened', default=23456, type=int)
AGP.add_argument('--dbstring', help='Database connection string', type=str)
AGP.add_argument('--debug', help='debug mode', default=False, type=bool)
args, _ = AGP.parse_known_args()

app = Flask(__name__)
app.config.from_object(__name__)
Bootstrap(app)

engine = create_engine(args.dbstring, echo=True)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form['name'] != '':
            name = request.form['name']
            new_environment = Environments(name=name)
            try:
                session.add(new_environment)
                session.commit()
                return redirect('/')
            except Exception as Ex:
                return "There was a problem adding new record."
        else:
            return "Empty environment name."
    elif request.method == 'GET':
        env = session.query(Environments).order_by(Environments.id).all()
        topics = session.query(
            Topics.topic_id,
            Topics.topic_name,
            Topics.zulip_to,
            Topics.zulip_subject,
            Templates.template_name)\
            .filter(Topics.templ_id == Templates.template_id).order_by(Topics.topic_id).all()
        return render_template('index.html', env=env, topics=topics)


@app.route('/env/delete/<int:id>', methods=['GET', 'POST'])
def env_delete(id):
    environment = session.query(Environments).get(ident=id)
    if request.method == 'POST':
        session.delete(environment)
        session.commit()
        return jsonify(status='ok')
    return render_template('/snippets/env_delete.html', title="Deleting Environment Permanently", env=environment)


@app.route('/env/update/<int:id>', methods=['GET', 'POST'])
def env_update(id):
    environment = session.query(Environments).get(ident=id)
    form = EnvUpdateForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        environment.name = form.name.data
        session.commit()
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
