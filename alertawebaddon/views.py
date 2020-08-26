import json

from flask import jsonify, url_for, flash
from flask import render_template, request, redirect
from flask_dance.contrib.github import make_github_blueprint, github

from alertawebaddon import app, db
from alertawebaddon.forms import EnvUpdateForm, TopicUpdateForm, TemplateUpdateForm
from alertawebaddon.model import Environments, Topics, Templates, get_last_id

db.create_all()
github_bp = make_github_blueprint(redirect_url=app.config['PROXY_PREFIX_PATH'])


@app.route('/', methods=['GET'])
def index():
    if not github.authorized:
        return redirect(url_for('github.login'))
    username = github.get('/user').json()['login']
    orgs = json.loads(github.get(f'/users/{username}/orgs').text)
    for org in orgs:
        if app.config.get('GITHUB_OAUTH_ALLOWED_ORGANIZATIONS') in org['login']:
            return render_template('index.html')
    return render_template('403page.html')


@app.route('/environments', methods=['GET'])
def environments():
    if not github.authorized:
        return redirect(url_for('github.login'))
    username = github.get('/user').json()['login']
    orgs = json.loads(github.get(f'/users/{username}/orgs').text)
    for org in orgs:
        if app.config.get('GITHUB_OAUTH_ALLOWED_ORGANIZATIONS') in org['login']:
            env = db.session.query(Environments).order_by(Environments.id).all()
            return render_template('snippets/environments.html', env=env)
    return render_template('403page.html')


@app.route('/templates', methods=['GET'])
def templates():
    if not github.authorized:
        return redirect(url_for('github.login'))
    username = github.get('/user').json()['login']
    orgs = json.loads(github.get(f'/users/{username}/orgs').text)
    for org in orgs:
        if app.config.get('GITHUB_OAUTH_ALLOWED_ORGANIZATIONS') in org['login']:
            templates = db.session.query(Templates).order_by(Templates.template_id).all()
            return render_template('snippets/templates.html', templates=templates)
    return render_template('403page.html')


@app.route('/topics', methods=['GET'])
def topics():
    if not github.authorized:
        return redirect(url_for('github.login'))
    username = github.get('/user').json()['login']
    orgs = json.loads(github.get(f'/users/{username}/orgs').text)
    for org in orgs:
        if app.config.get('GITHUB_OAUTH_ALLOWED_ORGANIZATIONS') in org['login']:
            topics = db.session.query(
                Topics.topic_id,
                Topics.topic_name,
                Topics.zulip_to,
                Topics.zulip_subject,
                Templates.template_name,
                Environments.name,
                Topics.skip) \
                .filter(Topics.template_id == Templates.template_id, Topics.environment_id == Environments.id).order_by(
                Topics.topic_name).all()
            templates = db.session.query(Templates).order_by(Templates.template_id).all()
            env = db.session.query(Environments).order_by(Environments.id).all()
            return render_template('snippets/topics.html', templates=templates, topics=topics, env=env)
    return render_template('403page.html')


@app.route('/env/add', methods=['POST'])
def env_add():
    if request.form['NewEnvName'] != '':
        name = request.form['NewEnvName']
        new_environment = Environments(id=get_last_id(db.session, Environments)[0] + 1, name=name)
        try:
            db.session.add(new_environment)
            db.session.commit()
            return redirect(url_for('environments'))
        except Exception as Ex:
            return 'There was a problem adding new record.'
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
    return render_template('/snippets/env_delete.html', title='Deleting Environment Permanently', env=environment)


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
    return render_template('/snippets/env_update.html', title='Edit Environment', form=form)


@app.route('/topic/add', methods=['POST'])
def topic_add():
    if request.form['newTopicName'] != '' and request.form['newTopicZulipTo'] != '' \
            and request.form['newTopicZulipSubject'] != '' and request.form['newTopicTemplate'] != '' \
            and request.form['newTopicEnv'] != '' and request.form['newTopicSkip'] != '':
        new_topic = Topics(topic_id=get_last_id(db.session, Topics)[0] + 1,
                           topic_name=request.form['newTopicName'],
                           zulip_to=request.form['newTopicZulipTo'],
                           zulip_subject=request.form['newTopicZulipSubject'],
                           template_id=db.session.query(Templates.template_id).
                           filter(request.form['newTopicTemplate'] == Templates.template_name).scalar(),
                           environment_id=db.session.query(Environments.id).
                           filter(request.form['newTopicEnv'] == Environments.name).scalar(),
                           skip=bool(int(request.form['newTopicSkip'])))
        try:
            db.session.add(new_topic)
            db.session.commit()
            return redirect(url_for('topics'))
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
        topic.template_id = int(form.ftemplate.data)
        topic.environment_id = int(form.fenvironment_name.data)
        topic.skip = form.fskip.data
        db.session.commit()
        return jsonify(status='ok')
    elif request.method == 'GET':
        form.ftopic_name.data = topic.topic_name
        form.fzulip_to.data = topic.zulip_to
        form.fzulip_subject.data = topic.zulip_subject
        templates = [(template.template_id, template.template_name) for template in
                     db.session.query(Templates.template_id, Templates.template_name).
                         order_by(Templates.template_id).all()]
        form.ftemplate.choices = sort_choices(templates, topic.template_id)
        envs = [(env.id, env.name) for env in db.session.query(Environments).order_by(Environments.id).all()]
        form.fenvironment_name.choices = sort_choices(envs, topic.environment_id)
        form.fskip.data = topic.skip
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
            return redirect(url_for('templates'))
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


@app.errorhandler(404)
def not_found(e):
    return render_template('404page.html')


def sort_choices(data: list, filter):
    data.insert(0, data.pop([x for x, y in enumerate(data) if y[0] == filter][0]))
    return data
