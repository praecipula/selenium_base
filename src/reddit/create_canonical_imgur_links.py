#!/usr/bin/env python

'''
This is simply to rewrite urls to the page (like "http://imgur.com/a/img.jpg" to "https://i.imgur.com/img.jpg"
'''
import urllib
import pathlib
from base import AutomationCommandBase, CommandParser
from reddit.image_post_data_storage import Storage, RedditImagePost

import logging
LOG = logging.getLogger(__name__)

class RedditNormalizeImageLocations(AutomationCommandBase):
    '''
    Normalize image locations.
    There is logic based on the url and the canonical location here:
    1) If it's an imgur image at i.imgur.com/[something].ext then it's already canonical
    2) If it's an imgur image at imgur.com/[something].ext then it simply needs to refer to i.imgur.com instead for the plain image
    3) If it's an imgur image at imgur.com/[something] (no extension) then we can't munge the filename and have to scrape the page for the real image location
    4) If it's a reddit image post there's no outgoing image at all, and we need to visit the reddit post to scrape the image.
    5) If it's a gifycat, well I don't know yet.

    This class will do all that and possibly download the image.
    '''
    name = "reddit_normalize_image_locations"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("num_posts", metavar='POSTS', nargs='?', type=int, default=20)

    def __init__(self, command_args):
        super().__init__(command_args)
        self._num_posts = self._args.num_posts

    def handle_complete_imgur_link(self, post):
        '''
        An imgur link is "complete" when we can get the canonical link solely from the existing url.
        That means it references an image by the image's ID and differs only in the http vs. https.
        '''
        LOG.info("Imgur post seems to have complete image url; we don't need to visit in the browser to set the canonical one")
        url = urllib.parse.urlparse(post.image_url)
        post.canonical_media_url = f"https://i.imgur.com{url.path}"

    def handle_imgur_page_before_image(self, post):
        LOG.warning("TODO: implement visiting imgur page")



    def execute(self):
        normalized = Storage.session().query(RedditImagePost). \
                filter(RedditImagePost.image_url.like("%imgur%")). \
                filter(RedditImagePost.image_url.notlike("%i.imgur%")). \
                limit(self._num_posts).all()
        for i in range(self._num_posts):
            post = normalized[i]
            LOG.info(f"Raw image link is {post.image_url}")
            url = urllib.parse.urlparse(post.image_url)
            if "imgur" in url.netloc:
                if pathlib.Path(url.path).suffix == '':
                    self.handle_imgur_page_before_image(post)
                else:
                    self.handle_complete_imgur_link(post)
            LOG.info(f"Canonical media link is {post.canonical_media_url}")
            #Storage.session().commit()
        return True
