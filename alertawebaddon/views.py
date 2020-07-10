import json
import os

from flask import jsonify, url_for, flash
from flask import render_template, request, redirect
from flask_dance.contrib.github import make_github_blueprint, github

from alertawebaddon import app, db
from alertawebaddon.forms import EnvUpdateForm, TopicUpdateForm, TemplateUpdateForm, SkipUpdateForm
from alertawebaddon.model import Environments, Topics, Templates, TopicsToSkip, get_last_id

GF_AUTH_GITHUB_ALLOWED_ORGANIZATIONS = \
    os.environ.get("GF_AUTH_GITHUB_ALLOWED_ORGANIZATIONS", default="opentelekomcloud-infra")
db.create_all()
github_bp = make_github_blueprint()


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if not github.authorized:
        return redirect(url_for("github.login"))
    username = github.get("/user").json()['login']
    orgs = json.loads(github.get(f"/users/{username}/orgs").text)
    for org in orgs:
        if GF_AUTH_GITHUB_ALLOWED_ORGANIZATIONS in org['login']:
            if path == '':
                return render_template('index.html')
            elif path == 'environments':
                env = db.session.query(Environments).order_by(Environments.id).all()
                return render_template('snippets/environments.html', env=env)
            elif path == 'templates':
                templates = db.session.query(Templates).order_by(Templates.template_id).all()
                return render_template('snippets/templates.html', templates=templates)
            elif path == 'topics':
                topics = db.session.query(
                    Topics.topic_id,
                    Topics.topic_name,
                    Topics.zulip_to,
                    Topics.zulip_subject,
                    Templates.template_name) \
                    .filter(Topics.templ_id == Templates.template_id).order_by(Topics.topic_id).all()
                templates = db.session.query(Templates).order_by(Templates.template_id).all()
                return render_template('snippets/topics.html', templates=templates, topics=topics)
            elif path == 'skips':
                topics_to_skip = db.session.query(
                    TopicsToSkip.id,
                    TopicsToSkip.skip,
                    Environments.name,
                    Topics.topic_name) \
                    .filter(TopicsToSkip.environment_id == Environments.id, TopicsToSkip.topic_id == Topics.topic_id) \
                    .order_by(Environments.id).all()
                env = db.session.query(Environments).order_by(Environments.id).all()
                topics = db.session.query(
                    Topics.topic_id,
                    Topics.topic_name,
                    Topics.zulip_to,
                    Topics.zulip_subject,
                    Templates.template_name) \
                    .filter(Topics.templ_id == Templates.template_id).order_by(Topics.topic_id).all()
                return render_template('snippets/topics_skip.html', skip=topics_to_skip, env=env, topics=topics)
            else:
                return render_template('404page.html')
    return render_template('403page.html')


@app.route('/env/add', methods=['POST'])
def env_add():
    if request.form['NewEnvName'] != '':
        name = request.form['NewEnvName']
        new_environment = Environments(id=get_last_id(db.session, Environments)[0] + 1, name=name)
        try:
            db.session.add(new_environment)
            db.session.commit()
            return redirect('/environments')
        except Exception as Ex:
            return "There was a problem adding new record."
    else:
        flash('Empty environment name.')
        return redirect(url_for('environments'))


@app.route('/env/delete/<int:id>', methods=['GET', 'POST'])
def env_delete(id):
    environment = db.session.query(Environments).get(ident=id)
    if request.method == 'POST':
        db.session.delete(environment)
        db.session.commit()
        return jsonify(status='ok')
    return render_template('/snippets/env_delete.html', title="Deleting Environment Permanently", env=environment)


@app.route('/env/update/<int:id>', methods=['GET', 'POST'])
def env_update(id):
    environment = db.session.query(Environments).get(ident=id)
    form = EnvUpdateForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        environment.name = form.fname.data
        db.session.commit()
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
        new_topic = Topics(topic_id=get_last_id(db.session, Topics)[0] + 1,
                           topic_name=request.form['newTopicName'],
                           zulip_to=request.form['newTopicName'],
                           zulip_subject=request.form['newTopicName'],
                           templ_id=db.session.query(Templates.template_id).
                           filter(request.form['newTopicTemplate'] == Templates.template_name).scalar())
        try:
            db.session.add(new_topic)
            db.session.commit()
            return redirect('/topics')
        except Exception as Ex:
            return 'There was a problem adding new record.'
    else:
        flash('Fields should not be empty!')
        return redirect(url_for('topics'))


@app.route('/topic/delete/<int:id>', methods=['GET', 'POST'])
def topic_delete(id):
    topic = db.session.query(Topics).get(ident=id)
    if request.method == 'POST':
        db.session.delete(topic)
        db.session.commit()
        return jsonify(status='ok')
    return render_template('/snippets/topic_delete.html', title='Deleting Topic Permanently', topic=topic)


@app.route('/topic/update/<int:id>', methods=['GET', 'POST'])
def topic_update(id):
    topic = db.session.query(Topics).get(ident=id)
    form = TopicUpdateForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        topic.topic_name = form.ftopic_name.data
        topic.zulip_to = form.fzulip_to.data
        topic.zulip_subject = form.fzulip_subject.data
        topic.templ_id = int(form.ftemplate.data)
        db.session.commit()
        return jsonify(status='ok')
    elif request.method == 'GET':
        form.ftopic_name.data = topic.topic_name
        form.fzulip_to.data = topic.zulip_to
        form.fzulip_subject.data = topic.zulip_subject
        templates = [(template.template_id, template.template_name) for template in
                     db.session.query(Templates.template_id, Templates.template_name).
                         order_by(Templates.template_id).all()]
        form.ftemplate.choices = sort_choices(templates, topic.templ_id)
    else:
        data = json.dumps(form.errors, ensure_ascii=False)
        return jsonify(data)
    return render_template('/snippets/topic_update.html', title='Edit Topic', form=form)


@app.route('/template/add', methods=['POST'])
def template_add():
    if request.form['newTemplateName'] != '' and request.form['newTemplateData'] != '':
        new_topic = Templates(template_id=get_last_id(db.session, Templates)[0] + 1,
                              template_name=request.form['newTemplateName'],
                              template_data=request.form['newTemplateData'])
        try:
            db.session.add(new_topic)
            db.session.commit()
            return redirect('/templates')
        except Exception as Ex:
            return 'There was a problem adding new record.'
    else:
        flash('Fields should not be empty!')
        return redirect(url_for('templates'))


@app.route('/template/delete/<int:id>', methods=['GET', 'POST'])
def template_delete(id):
    template = db.session.query(Templates).get(ident=id)
    if request.method == 'POST':
        db.session.delete(template)
        db.session.commit()
        return jsonify(status='ok')
    return render_template('/snippets/template_delete.html', title='Deleting Template Permanently', template=template)


@app.route('/template/update/<int:id>', methods=['GET', 'POST'])
def template_update(id):
    template = db.session.query(Templates).get(ident=id)
    form = TemplateUpdateForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        template.template_name = form.ftemplate_name.data
        template.template_data = form.ftemplate_data.data
        db.session.commit()
        return jsonify(status='ok')
    elif request.method == 'GET':
        form.ftemplate_name.data = template.template_name
        form.ftemplate_data.data = template.template_data
    else:
        data = json.dumps(form.errors, ensure_ascii=False)
        return jsonify(data)
    return render_template('/snippets/template_update.html', title='Edit Template', form=form)


@app.route('/skip/add', methods=['POST'])
def skip_add():
    if request.form['newSkip'] != '' and request.form['newSkipTopic'] != '' and request.form['newSkipEnv'] != '':
        new_skip = TopicsToSkip(id=get_last_id(db.session, TopicsToSkip)[0] + 1,
                                skip=bool(int(request.form['newSkip'])),
                                environment_id=db.session.query(Environments.id).
                                filter(request.form['newSkipEnv'] == Environments.name).scalar(),
                                topic_id=db.session.query(Topics.topic_id).
                                filter(request.form['newSkipTopic'] == Topics.topic_name).scalar())
        try:
            db.session.add(new_skip)
            db.session.commit()
            return redirect('/skips')
        except Exception as Ex:
            return 'There was a problem adding new record.'
    else:
        flash('Fields should not be empty!')
        return redirect(url_for('skips'))


@app.route('/skip/delete/<int:id>', methods=['GET', 'POST'])
def skip_delete(id):
    skip = db.session.query(TopicsToSkip).get(ident=id)
    topic = db.session.query(Topics.topic_name).filter(skip.topic_id == Topics.topic_id).scalar()
    env = db.session.query(Environments.name).filter(skip.environment_id == Environments.id).scalar()
    if request.method == 'POST':
        db.session.delete(skip)
        db.session.commit()
        return jsonify(status='ok')
    return render_template('/snippets/skip_delete.html', title='Deleting Blackout Status for Topic Permanently',
                           skip=skip, topic=topic, env=env)


@app.route('/skip/update/<int:id>', methods=['GET', 'POST'])
def skip_update(id):
    skip = db.session.query(TopicsToSkip).get(ident=id)
    form = SkipUpdateForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        skip.skip = form.fskip.data
        skip.environment_id = int(form.fenvironment_name.data)
        skip.topic_id = int(form.ftopic_name.data)
        db.session.commit()
        return jsonify(status='ok')
    elif request.method == 'GET':
        form.fskip.data = skip.skip

        envs = [(env.id, env.name) for env in db.session.query(Environments).order_by(Environments.id).all()]
        form.fenvironment_name.choices = sort_choices(envs, skip.environment_id)

        topics = [(topic.topic_id, topic.topic_name) for topic in
                  db.session.query(Topics).order_by(Topics.topic_id).all()]
        form.ftopic_name.choices = sort_choices(topics, skip.topic_id)
    else:
        data = json.dumps(form.errors, ensure_ascii=False)
        return jsonify(data)
    return render_template('/snippets/skip_update.html', title='Edit Blackout Status for Topic', form=form)


def sort_choices(data: list, filter):
    data.insert(0, data.pop([x for x, y in enumerate(data) if y[0] == filter][0]))
    return data
