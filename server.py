import json
from argparse import ArgumentParser
from threading import Thread

from flask import Flask, jsonify
from flask import render_template, request, redirect
from flask_bootstrap import Bootstrap
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from forms import EnvUpdateForm, TopicUpdateForm, TemplateUpdateForm, SkipUpdateForm
from model import Environments, Topics, Templates, TopicsToSkip, get_pk_name, get_last_id

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
        return render_template('index.html')


@app.route('/environments', methods=['GET'])
def environments():
    if request.method == 'GET':
        env = session.query(Environments).order_by(Environments.id).all()
        return render_template('snippets/environments.html', env=env)


@app.route('/topics', methods=['GET'])
def topics():
    if request.method == 'GET':
        topics = session.query(
            Topics.topic_id,
            Topics.topic_name,
            Topics.zulip_to,
            Topics.zulip_subject,
            Templates.template_name) \
            .filter(Topics.templ_id == Templates.template_id).order_by(Topics.topic_id).all()
        templates = session.query(Templates).order_by(Templates.template_id).all()
        return render_template('snippets/topics.html', templates=templates, topics=topics)


@app.route('/templates', methods=['GET'])
def templates():
    if request.method == 'GET':
        templates = session.query(Templates).order_by(Templates.template_id).all()
        return render_template('snippets/templates.html', templates=templates)


@app.route('/skips', methods=['GET'])
def skips():
    if request.method == 'GET':
        topics_to_skip = session.query(
            TopicsToSkip.id,
            TopicsToSkip.skip,
            Environments.name,
            Topics.topic_name) \
            .filter(TopicsToSkip.environment_id == Environments.id, TopicsToSkip.topic_id == Topics.topic_id) \
            .order_by(Environments.id).all()
        env = session.query(Environments).order_by(Environments.id).all()
        topics = session.query(
            Topics.topic_id,
            Topics.topic_name,
            Topics.zulip_to,
            Topics.zulip_subject,
            Templates.template_name) \
            .filter(Topics.templ_id == Templates.template_id).order_by(Topics.topic_id).all()
        return render_template('snippets/topics_skip.html', skip=topics_to_skip, env=env, topics=topics)


@app.route('/env/add', methods=['POST'])
def env_add():
    if request.form['NewEnvName'] != '':
        name = request.form['NewEnvName']
        new_environment = Environments(id=get_last_id(session, Environments)[0] + 1, name=name)
        try:
            session.add(new_environment)
            session.commit()
            return redirect('/environments')
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
        new_topic = Topics(topic_id=get_last_id(session, Topics)[0] + 1,
                           topic_name=request.form['newTopicName'],
                           zulip_to=request.form['newTopicName'],
                           zulip_subject=request.form['newTopicName'],
                           templ_id=session.query(Templates.template_id).
                           filter(request.form['newTopicTemplate'] == Templates.template_name).scalar())
        try:
            session.add(new_topic)
            session.commit()
            return redirect('/topics')
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
        form.ftemplate.choices.insert(0, form.ftemplate.choices.pop(
            [x for x, y in enumerate(form.ftemplate.choices) if y[0] == topic.templ_id][0]))
    else:
        data = json.dumps(form.errors, ensure_ascii=False)
        return jsonify(data)
    return render_template('/snippets/topic_update.html', title="Edit Topic", form=form)


@app.route('/template/add', methods=['POST'])
def template_add():
    if request.form['newTemplateName'] != '' and request.form['newTemplateData'] != '':
        new_topic = Templates(template_id=get_last_id(session, Templates)[0] + 1,
                              template_name=request.form['newTemplateName'],
                              template_data=request.form['newTemplateData'])
        try:
            session.add(new_topic)
            session.commit()
            return redirect('/templates')
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


@app.route('/skip/add', methods=['POST'])
def skip_add():
    if request.form['newSkip'] != '' and request.form['newSkipTopic'] != '' and request.form['newSkipEnv'] != '':
        new_skip = TopicsToSkip(id=get_last_id(session, TopicsToSkip)[0] + 1,
                                skip=bool(int(request.form['newSkip'])),
                                environment_id=session.query(Environments.id).
                                filter(request.form['newSkipEnv'] == Environments.name).scalar(),
                                topic_id=session.query(Topics.topic_id).
                                filter(request.form['newSkipTopic'] == Topics.topic_name).scalar())
        try:
            session.add(new_skip)
            session.commit()
            return redirect('/skips')
        except Exception as Ex:
            return "There was a problem adding new record."
    else:
        return "Empty values."


@app.route('/skip/delete/<int:id>', methods=['GET', 'POST'])
def skip_delete(id):
    skip = session.query(TopicsToSkip).get(ident=id)
    topic = session.query(Topics.topic_name).filter(skip.topic_id == Topics.topic_id).scalar()
    env = session.query(Environments.name).filter(skip.environment_id == Environments.id).scalar()
    if request.method == 'POST':
        session.delete(skip)
        session.commit()
        return jsonify(status='ok')
    return render_template('/snippets/skip_delete.html', title="Deleting Blackout Status for Topic Permanently",
                           skip=skip, topic=topic, env=env)


@app.route('/skip/update/<int:id>', methods=['GET', 'POST'])
def skip_update(id):
    skip = session.query(TopicsToSkip).get(ident=id)
    form = SkipUpdateForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        skip.skip = form.fskip.data
        skip.environment_id = int(form.fenvironment_name.data)
        skip.topic_id = int(form.ftopic_name.data)
        session.commit()
        return jsonify(status='ok')
    elif request.method == 'GET':
        form.fskip.data = skip.skip
        form.fenvironment_name.choices = [(env.id, env.name) for env in session.query(Environments)
            .order_by(Environments.id).all()]
        form.fenvironment_name.choices.insert(0, form.fenvironment_name.choices.pop(
            [x for x, y in enumerate(form.fenvironment_name.choices) if y[0] == skip.environment_id][0]))
        form.ftopic_name.choices = [(topic.topic_id, topic.topic_name) for topic in session.query(Topics)
            .order_by(Topics.topic_id).all()]
        form.ftopic_name.choices.insert(0, form.ftopic_name.choices.pop(
            [x for x, y in enumerate(form.ftopic_name.choices) if y[0] == skip.topic_id][0]))
    else:
        data = json.dumps(form.errors, ensure_ascii=False)
        return jsonify(data)
    return render_template('/snippets/skip_update.html', title="Edit Blackout Status for Topic", form=form)


def main():
    Thread(target=app.run, kwargs={'port': args.port, 'debug': args.debug}).start()


if __name__ == '__main__':
    main()
