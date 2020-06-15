import json
from argparse import ArgumentParser
from threading import Thread

from flask import Flask, jsonify
from flask import render_template, request, redirect
from flask_bootstrap import Bootstrap
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from forms import EnvUpdateForm, TopicUpdateForm, TemplateUpdateForm
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


@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        env = session.query(Environments).order_by(Environments.id).all()
        topics = session.query(
            Topics.topic_id,
            Topics.topic_name,
            Topics.zulip_to,
            Topics.zulip_subject,
            Templates.template_name) \
            .filter(Topics.templ_id == Templates.template_id).order_by(Topics.topic_id).all()
        templates = session.query(Templates).order_by(Templates.template_id).all()
        topics_to_skip = session.query(
            TopicsToSkip.id,
            TopicsToSkip.skip,
            Environments.name,
            Topics.topic_name) \
            .filter(TopicsToSkip.environment_id == Environments.id, TopicsToSkip.topic_id == Topics.topic_id) \
            .order_by(Environments.id).all()
        return render_template('index.html', env=env, topics=topics, templates=templates, skip=topics_to_skip)


@app.route('/env/add', methods=['POST'])
def env_add():
    if request.form['NewEnvName'] != '':
        name = request.form['NewEnvName']
        new_environment = Environments(id=get_last_id(Environments) + 1, name=name)
        try:
            session.add(new_environment)
            session.commit()
            return redirect('/')
        except Exception as Ex:
            return "There was a problem adding new record."
    else:
        return "Empty environment name."


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
        environment.name = form.fname.data
        session.commit()
        return jsonify(status='ok')
    elif request.method == 'GET':
        form.fname.data = environment.name
    else:
        data = json.dumps(form.errors, ensure_ascii=False)
        return jsonify(data)
    return render_template('/snippets/env_update.html', title="Edit Environment", form=form)


@app.route('/topic/add', methods=['POST'])
def topic_add():
    if request.form['newTopicName'] != '' and request.form['newTopicZulipTo'] != '' \
            and request.form['newTopicZulipSubject'] != '' and request.form['newTopicTemplate'] != '':
        new_topic = Topics(topic_id=get_last_id(Topics) + 1,
                           topic_name=request.form['newTopicName'],
                           zulip_to=request.form['newTopicName'],
                           zulip_subject=request.form['newTopicName'],
                           templ_id=session.query(Templates.template_id).
                           filter(request.form['newTopicTemplate'] == Templates.template_name).scalar())
        try:
            session.add(new_topic)
            session.commit()
            return redirect('/')
        except Exception as Ex:
            return "There was a problem adding new record."
    else:
        return "Empty topic name."


@app.route('/topic/delete/<int:id>', methods=['GET', 'POST'])
def topic_delete(id):
    topic = session.query(Topics).get(ident=id)
    if request.method == 'POST':
        session.delete(topic)
        session.commit()
        return jsonify(status='ok')
    return render_template('/snippets/topic_delete.html', title="Deleting Topic Permanently", topic=topic)


@app.route('/topic/update/<int:id>', methods=['GET', 'POST'])
def topic_update(id):
    topic = session.query(Topics).get(ident=id)
    form = TopicUpdateForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        topic.topic_name = form.ftopic_name.data
        topic.zulip_to = form.fzulip_to.data
        topic.zulip_subject = form.fzulip_subject.data
        topic.templ_id = int(form.ftemplate.data)
        session.commit()
        return jsonify(status='ok')
    elif request.method == 'GET':
        form.ftopic_name.data = topic.topic_name
        form.fzulip_to.data = topic.zulip_to
        form.fzulip_subject.data = topic.zulip_subject
        form.ftemplate.choices = [(template.template_id, template.template_name) for template in
                                  session.query(Templates.template_id, Templates.template_name).
                                      order_by(Templates.template_id).all()]
        form.ftemplate.default = session.query(Templates.template_name) \
            .filter(topic.templ_id == Templates.template_id).scalar()
    else:
        data = json.dumps(form.errors, ensure_ascii=False)
        return jsonify(data)
    return render_template('/snippets/topic_update.html', title="Edit Topic", form=form)


@app.route('/template/add', methods=['POST'])
def template_add():
    if request.form['newTemplateName'] != '' and request.form['newTemplateData'] != '':
        new_topic = Templates(template_id=get_last_id(Templates) + 1,
                              template_name=request.form['newTemplateName'],
                              template_data=request.form['newTemplateData'])
        try:
            session.add(new_topic)
            session.commit()
            return redirect('/')
        except Exception as Ex:
            return "There was a problem adding new record."
    else:
        return "Empty template name."


@app.route('/template/delete/<int:id>', methods=['GET', 'POST'])
def template_delete(id):
    template = session.query(Templates).get(ident=id)
    if request.method == 'POST':
        session.delete(template)
        session.commit()
        return jsonify(status='ok')
    return render_template('/snippets/template_delete.html', title="Deleting Template Permanently", template=template)


@app.route('/template/update/<int:id>', methods=['GET', 'POST'])
def template_update(id):
    template = session.query(Templates).get(ident=id)
    form = TemplateUpdateForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        template.template_name = form.ftemplate_name.data
        template.template_data = form.ftemplate_data.data
        session.commit()
        return jsonify(status='ok')
    elif request.method == 'GET':
        form.ftemplate_name.data = template.template_name
        form.ftemplate_data.data = template.template_data
    else:
        data = json.dumps(form.errors, ensure_ascii=False)
        return jsonify(data)
    return render_template('/snippets/template_update.html', title="Edit Template", form=form)


def get_last_id(table):
    return session.query(table).count()


def main():
    Thread(target=app.run, kwargs={'port': args.port, 'debug': args.debug}).start()


if __name__ == '__main__':
    main()
