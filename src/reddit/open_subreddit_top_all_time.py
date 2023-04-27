from base import driver, By, Keys, ActionChains, AutomationCommandBase, CommandParser, ASSERT
from base.repl import drop_into_repl
import logging
import yaml
import time

from reddit import RedditBase

LOG = logging.getLogger(__name__)


class RedditOpenSubredditTopAllTime(RedditBase):
    name = "reddit_open_subreddit_top_all_time"

    subreddit_url_prefix = "https://www.reddit.com/r/"
    subreddit_url_top_all_time_suffix = "/top/?t=all"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("subreddit", metavar='SUBREDDIT', type=str)

    def __init__(self, command_args):
        super().__init__(command_args)
        self._subreddit = self._args.subreddit


    def execute(self):
        LOG.info(f"Going to all time top posts for {self._subreddit}")
        driver().get(RedditOpenSubredditTopAllTime.subreddit_url_prefix + \
                self._subreddit + \
                RedditOpenSubredditTopAllTime.subreddit_url_top_all_time_suffix)

        return True

    def __str__(self):
        return f"{self.__class__.name}: {self._args}"

