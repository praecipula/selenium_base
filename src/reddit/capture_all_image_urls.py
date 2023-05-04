from base import driver, By, Keys, ActionChains, AutomationCommandBase, CommandParser, ASSERT
from base.repl import drop_into_repl
import logging
import yaml
import time

from reddit import RedditBase
from reddit.image_post_data_storage import RedditSubreddit, RedditImagePost

LOG = logging.getLogger(__name__)


class RedditCaptureAllImageUrls(RedditBase):
    name = "reddit_capture_all_image_urls"

    parser = CommandParser(prog = name, description=f'{name} command')

    def __init__(self, command_args):
        super().__init__(command_args)

    def process_post(self, post, subreddit):
        LOG.info(f"Processing post with element id {post.get_attribute('id')}")
        if post.get_attribute('id') == 'adblocktest':
            # This appears to be a test for whether we're blocking dynamic loading of ads.
            # As it turns out, we're not, but this is a dummy post we should skip.
            LOG.info("Skipping ad block test post")
            return True
        links = self.elements_by_xpath(".//a", post)
        image_url = None
        post_path = None
        post_user = None
        post_title = None
        for link in links:
            target = link.get_attribute("href")
            LOG.debug(f"Processing post link pointing to {target}")
            if link.get_attribute('data-click-id') == 'user':
                LOG.debug(f"It's a user link")
                # This is a link to the user who posted this
                post_user = target
            elif link.get_attribute('data-click-id') == 'body':
                LOG.debug(f"It's a link to the long-form post")
                # *Very dirty* check for whether this is the one we want; doesn't incur selenium default wait though.
                if not "<h3" in link.get_attribute('innerHTML'):
                    LOG.info("Long form link found but no title; assuming another link has the title embedded in it.")
                    continue
                # This is the link to the actual longer-form post. It has some good stuff.
                post_title = self.element_by_xpath(".//h3", link).get_attribute('innerHTML')
                post_path = target
            elif 'styled-outbound-link' in link.get_attribute('class'):
                LOG.debug(f"It's the link to the external image")
                # This is the link to the external image; what we're here for!
                image_url = target
        post_upvotes = self.elements_by_xpath(".//div[contains(@id, 'vote-arrows')]/div", post)[0].get_attribute('innerHTML')
        # Here we check if there's a link to the longer-form post. The body click parameter doesn't exist for ads, so we will have no path.
        # That's OK, we didn't want them anyway.
        if post_path != None:
            post = RedditImagePost.upsert(post_path, post_title, post_upvotes, post_user, subreddit, image_url)
        return True

    def execute(self):
        current_subreddit = RedditSubreddit.find_or_create_by_url(driver().current_url)
        LOG.info("Creating entries for all the images on {current_subreddit}")
        # This gets all posts that have outbound links.
        # Do we even want this? All posts will get all inside and outside links.
        # Now that I think of it, we want that - what if Reddit brings down whole subreddits?
        posts_xpath = "//div[contains(@class, 'Post')]"
        posts = self.elements_by_xpath(posts_xpath)
        for post in posts:
            self.process_post(post, current_subreddit)
        return True

    def __str__(self):
        return f"{self.__class__.name}: {self._args}"

