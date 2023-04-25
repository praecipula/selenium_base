
import os
import urllib
import re

import logging
LOG = logging.getLogger(__name__)

from base import AutomationCommandBase, CommandParser, ASSERT

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index, event, select
from sqlalchemy.orm import relationship, backref, declarative_base, sessionmaker
from sqlalchemy.sql import func, expression

Base = declarative_base()

class Storage(AutomationCommandBase):
    '''
    This class manages all the database work to be done for downloading and storing these images.
    At first we just create records of the image locations, then later we'll have workers that
    actually go and get the images. This is done in order to avoid downloading too many images
    all at once from a single IP.
    '''

    name = "reddit_storage"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("stats", action='store_true')

    db_file_name=os.path.dirname(__file__) + "/img_post_data.sqlite"

    @classmethod
    def initialize_db(cls):
        cls._engine = sqlalchemy.create_engine("sqlite:///" + cls.db_file_name, echo=True)
        Session = sessionmaker()
        Session.configure(bind=cls._engine)
        cls._session = Session()
        # This appears to be idempotent, at least for sqlite, so we'll call it every initialize.
        Base.metadata.create_all(cls._engine)

    @classmethod
    def session(cls):
        if not hasattr(cls, "_session"):
            LOG.info("SqlLiteHandler has no session set; calling initialize()")
            Storage.initialize_db()
        return cls._session

    def execute(self):
        s = Storage.session()


class RedditSubreddit(Base):
    '''
    The subreddit in which the image is posted
    '''

    __tablename__ = "subreddit"
    id = Column(Integer, primary_key=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(String, nullable=False, unique=True)
    page_metadata = relationship("RedditImagePost", backref=backref("subbreddit"))

    __table_args__ = (
            Index('subreddit_name_index', 'name'),
            )

    @classmethod
    def name_from_url(cls, url):
        '''
        Convenience method to strip out a subreddit's name from a url
        '''
        url = urllib.parse.urlparse(url)
        path_regex = r'/r/(?P<name>[\w\-_]+)/.*'
        match = re.match(path_regex, url.path)
        ASSERT(match != None, "Could not find subreddit name from URL")
        return match['name']

    @classmethod
    def find_or_create(cls, subreddit_name):
        subreddits = Storage.session().query(cls).filter_by(name=subreddit_name).limit(2).all()
        if len(subreddits) == 0:
            #create and return
            LOG.info(f"No existing subreddit \"{subreddit_name}\"; creating")
            new_subreddit = RedditSubreddit(name=subreddit_name)
            Storage.session().add(new_subreddit)
            Storage.session().commit()
            return new_subreddit
        elif len(subreddits) > 1:
            LOG.warning(f"Multiple entries found for subreddit named {subreddit_name}; returning first")
            return subreddits[0]
        else:
            return subreddits[0]

    @classmethod
    def find_or_create_by_url(cls, url):
        subreddit_name = cls.name_from_url(url)
        return cls.find_or_create(subreddit_name)

class RedditImagePost(Base):
    '''
    The record of an image post.
    '''

    __tablename__ = "post"
    id = Column(Integer, primary_key=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    path = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    upvotes = Column(String, nullable=False)
    posted_by = Column(String) # Can be null if the user's deleted
    image_url = Column(String) # Can be null if this is an "internal" post.
    subreddit_id = Column(Integer, ForeignKey("subreddit.id"))

    __table_args__ = (
            Index('post_path_index', 'path'),
            )

    @classmethod
    def upsert(cls, path, title, upvotes, posted_by, subreddit, image_url = None):

        posts = Storage.session().query(RedditImagePost).filter_by(path=path).limit(2).all()
        if len(posts) == 0:
            #create and return
            LOG.debug(f"No existing post \"{path}\"; creating")
            new_post = cls(path = path, \
                           title = title, \
                           upvotes = upvotes, \
                           posted_by = posted_by, \
                           image_url = image_url, \
                           subreddit_id = subreddit.id)
            Storage.session().add(new_post)
            Storage.session().commit()
            return new_post
        else:
            if len(posts) > 1:
                LOG.warning(f"Multiple entries found for post at path {path}; returning first")
            post = posts[0]
            post.title = title
            post.upvotes = upvotes
            post.image_url = image_url
            post.subreddit_id = subreddit.id
            Storage.session().commit()
            return post
