from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea


class EnvUpdateForm(FlaskForm):
    fname = StringField('Name:', validators=[DataRequired()])


class TopicUpdateForm(FlaskForm):
    ftopic_name = StringField('Name:', validators=[DataRequired()])
    fzulip_to = StringField('ZulipTo:', validators=[DataRequired()])
    fzulip_subject = StringField('ZulipSubject:', validators=[DataRequired()])
    ftemplate = SelectField('Template:', validate_choice=False)
    fenvironment_name = SelectField('Environment name:', validate_choice=False)
    fskip = BooleanField('Skip status:')


class TemplateUpdateForm(FlaskForm):
    ftemplate_name = StringField('Name:', validators=[DataRequired()])
    ftemplate_data = StringField('TemplateData:', widget=TextArea(), validators=[DataRequired()])
