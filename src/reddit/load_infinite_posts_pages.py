from base import driver, By, Keys, ActionChains, AutomationCommandBase, CommandParser, ASSERT
from base.repl import drop_into_repl
import logging
import yaml
import time
import random

from reddit import RedditBase

LOG = logging.getLogger(__name__)


class RedditLoadInfinitePostsPages(RedditBase):
    name = "reddit_load_infinite_posts_pages"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("pages", metavar='PAGES', type=int)

    def __init__(self, command_args):
        super().__init__(command_args)
        self._pages = self._args.pages

    def do_scroll(self):
        # Go to login page
        LOG.info("Scrolling to page bottom ... ")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        return True

    def execute(self):
        LOG.info("Scrolling down {self._pages} pages... ")
        for i in range(self._pages):
            LOG.info(f"Scrolling: {i}")
            self.do_scroll()
            sleep_time =random.gauss(3,1) 
            LOG.debug(f"Sleeping for {sleep_time}")
            time.sleep(sleep_time) #To get the page to load. I'm not sure if there's a better way than waiting.
        return True

    def __str__(self):
        return f"{self.__class__.name}: {self._args}"

