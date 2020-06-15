from sqlalchemy import ForeignKey, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Environments(Base):
    __tablename__ = 'alerta_environments'
    id = Column(Integer, primary_key=True)
    name = Column(String())

    children = relationship("TopicsToSkip")

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return f"<Environment {self.id, self.name}>"


class Templates(Base):
    __tablename__ = 'templates'
    template_id = Column(Integer, primary_key=True, autoincrement=True)
    template_name = Column(String())
    template_data = Column(String())

    children = relationship("Topics")

    def __init__(self, template_name, template_data):
        self.template_name = template_name
        self.template_data = template_data

    def __repr__(self):
        return f"<Template {self.template_name, self.template_data}>"


class Topics(Base):
    __tablename__ = 'topics'

    topic_id = Column(Integer, primary_key=True, autoincrement=True)
    topic_name = Column(String())
    zulip_to = Column(String())
    zulip_subject = Column(String())
    templ_id = Column(Integer(), ForeignKey('templates.template_id'))

    children = relationship("TopicsToSkip")

    def __init__(self, topic_id, topic_name, zulip_to, zulip_subject, templ_id):
        self.topic_id = topic_id
        self.topic_name = topic_name
        self.zulip_to = zulip_to
        self.zulip_subject = zulip_subject
        self.templ_id = templ_id

    def __repr__(self):
        return f"<Topic {self.topic_id, self.topic_name, self.zulip_to, self.zulip_subject, self.templ_id}>"


class TopicsToSkip(Base):
    __tablename__ = 'skip_topics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    skip = Column(Boolean())
    environment_id = Column(String(), ForeignKey('alerta_environments.id'))
    topic_id = Column(String(), ForeignKey('topics.topic_id'))

    def __init__(self, skip, environment_id, topic_id):
        self.skip = skip
        self.environment_id = environment_id
        self.topic_id = topic_id

    def __repr__(self):
        return f"<Skip {self.skip, self.environment_id, self.topic_id}>"
