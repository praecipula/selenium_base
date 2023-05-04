#!/usr/bin/env python

'''
This is simply to rewrite urls to the page (like "http://imgur.com/a/img.jpg" to "https://i.imgur.com/img.jpg"
'''
import urllib
import pathlib
import time
import random
import glob
import difflib
from base import AutomationCommandBase, CommandParser, driver, ActionChains, By, selenium_implicit_wait_default
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from reddit.image_post_data_storage import Storage, RedditImagePost
import pyautogui


import logging
LOG = logging.getLogger(__name__)
# So verbose at debug level!
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)

class RedditNormalizeImageLocations(AutomationCommandBase):
    '''
    Normalize image locations.
    There is logic based on the url and the canonical location here:
    1) If it's an imgur image at i.imgur.com/[something].ext then it's already canonical
    2) If it's an imgur image at imgur.com/[something].ext then it simply needs to refer to i.imgur.com instead for the plain image
    3) If it's an imgur image at imgur.com/[something] (no extension) then we can't munge the filename and have to scrape the page for the real image location. There may be multiple images.
    4) If it's a reddit image post there's no outgoing image at all, and we need to visit the reddit post to scrape the image.
    5) If it's a gifycat, well I don't know yet.

    This class will do all that and possibly download the image.
    '''
    name = "reddit_normalize_image_locations"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("num_posts", metavar='POSTS', nargs='?', type=int, default=20)
    parser.add_argument("offset", metavar='POSTS', nargs='?', type=int, default=0)

    media_download_dir = pathlib.PurePath(__file__).parent / "media"
    screenshot_targets_dir = pathlib.PurePath(__file__).parent / "screenshot_targets"

    def __init__(self, command_args):
        super().__init__(command_args)
        self._num_posts = self._args.num_posts
        self._offset = self._args.offset

    def handle_complete_imgur_link(self, post):
        '''
        An imgur link is "complete" when we can get the canonical link solely from the existing url.
        That means it references an image by the image's ID and differs only in the http vs. https.
        '''
        LOG.info("Imgur post seems to have complete image url; we don't need to visit in the browser to set the canonical one")
        url = urllib.parse.urlparse(post.image_url)
        post.canonical_media_urls = f"https://i.imgur.com{url.path}"

    def scroll_to_bottom(self):
        # Go to login page
        LOG.info("Scrolling to page bottom ... ")
        driver().execute_script("window.scrollTo(0, document.body.scrollHeight)")
        return True

    def scroll_into_view(self, element):
        driver().execute_script("arguments[0].scrollIntoView(true);", element)

    def scroll_down(self, distance):
        driver().execute_script("window.scrollBy(0, arguments[0]);", distance)

    def handle_imgur_page_before_image(self, post):
        LOG.info("Visiting imgur page to get underlying image link")
        driver().get(post.image_url)
        chain = ActionChains(driver())

        # This page load is generally fast
        driver().implicitly_wait(4)
        yes_over_18_xpath = "//div[contains(@class, 'btn-wall--yes')]"
        elements = self.elements_by_xpath(yes_over_18_xpath)
        driver().implicitly_wait(selenium_implicit_wait_default)

        if not elements or len(elements) == 0:
            LOG.info("We weren't shown the confirmation button; page might be deleted? Trying just in case it wasn't flagged NSFW.")
            # We'll probably re-set this later, but just to be sure; go ahead and suspect it's deleted.
            post.canonical_media_urls = "[DELETED]"
        else:
            element = elements[0]
            chain.click(on_element=element)
            chain.perform()
        load_more = True
        while load_more:
            self.scroll_to_bottom()
            try:
                driver().implicitly_wait(2)
                button_xpath = "//button[contains(@class, 'loadMore')]"
                elements = self.elements_by_xpath(button_xpath)
                if elements and len(elements) > 0:
                    LOG.info("Clicking on 'Load More'")
                    chain.click(on_element=elements[0])
                    chain.perform()
                else:
                    # No more "load more" element found
                    LOG.info("No 'Load More' button found")
                    load_more = False
            except TimeoutException as e:
                load_more = False
            finally:
                driver().implicitly_wait(selenium_implicit_wait_default)
        # OK, all images in the collection should be on the screen, or at least told to load.
        # Oh bother, it seems to be dynamically loading the images on scroll and removing them from the DOM when unscrolled.
        # A little too smart. I think I'll have to gradually scroll down the page and deduplicate image links :(
        # Start by scrolling back to the top of the gallery so we build the set in order, top to bottom.
        # 404s will not match here; we should exit.
        gallery_xpath = "//div[contains(@class, 'Gallery-MainContainer')]"
        elements = self.elements_by_xpath(gallery_xpath)
        if not elements or len(elements) == 0:
            LOG.info("No images found. We're probably on a 404 page.")
            # OK, now we're pretty sure.
            post.canonical_media_urls = "[DELETED]"
            return False
        element = elements[0]
        self.scroll_into_view(element)
        #Back it up some to be sure we get the first on screen; I found it'd miss some at just-in-view.
        self.scroll_down(-500)

        # This is a hack; keep scrolling until we get the same sized set like a bunch of times (then we've scrolled to the end)
        images_xpath = "//img[contains(@class, 'image-placeholder')]"
        video_xpath = "//div[contains(@class, 'PostVideo-video-wrapper')]//source"
        # Use a dict with keys only and ignored values.
        # This is guaranteed to have unique keys and insertion-order-preserving semantics
        element_link_set = {}
        still_scrolling = True
        set_unchanged_count = 0
        unchanged_set_stop_count = 25
        scroll_length = 100
        while still_scrolling:
            self.scroll_down(100);
            try:
                # Since this retries automatically we can assume it won't take 25 iterations of 1 second timeouts to load new elements.
                driver().implicitly_wait(1)
                visible_elements = self.elements_by_xpath(images_xpath)
                if not visible_elements or len(visible_elements) == 0:
                    LOG.info("Didn't find picures; is there video?")
                    visible_elements = self.elements_by_xpath(video_xpath)
                if not visible_elements or len(visible_elements) == 0:
                    LOG.info("No pics or video; assume this is a dead end page")
                    return False
                previous_set_size = len(element_link_set)
                [element_link_set.update({e.get_attribute("src"): None}) for e in visible_elements]
            except StaleElementReferenceException as e:
                LOG.debug(f"Element reference went stale; we scrolled beyond the loading boundary; trying again")
                continue
            finally:
                driver().implicitly_wait(selenium_implicit_wait_default)
            LOG.debug(len(element_link_set))
            new_set_size = len(element_link_set)
            if new_set_size != previous_set_size:
                LOG.debug("New element added to set")
                set_unchanged_count = 0
            else:
                set_unchanged_count = set_unchanged_count + 1
            if set_unchanged_count > unchanged_set_stop_count:
                LOG.debug(f"Set unchanged for {unchanged_set_stop_count} iterations; stopping")
                still_scrolling = False

        # OK, now we can serialize onto the record.
        post.canonical_media_urls=",".join(element_link_set.keys())
        return True

    def handle_reddit_image_post(self, post):
        driver().get(post.path)
        # unique keys and preserves insertion order
        element_link_set = {}

        def find_element(xpath, source_attribute, technique_name):
            driver().implicitly_wait(3)
            elements = self.elements_by_xpath(xpath)
            driver().implicitly_wait(selenium_implicit_wait_default)
            if elements and len(elements) > 0:
                # Found one. Only one?
                if len(elements) > 1:
                    LOG.warning(f"Found more than one {technique_name} media. Interesting. Might be OK?")
                canonical_location = elements[0].get_attribute(source_attribute)
                LOG.info(f"{technique_name}: {post.path} =>\t{canonical_location}")
                element_link_set.update({canonical_location: None})
            else:
                LOG.info(f"Did not find {technique_name} media.")

        # First try to get a reddit-hosted image
        find_element("//img[contains(@class, 'ImageBox-image')]/parent::a", "href", "direct hosted normal")

        # Next, try to get a hosted animated gif or video
        if len(element_link_set) == 0:
            find_element("//video[contains(@class, 'media-element')]/parent::a", "href", "direct hosted video")

        # OK, it seems they can also be hosted in a "figure" tag
        if len(element_link_set) == 0:
            find_element("//figure/a", "href", "direct hosted figure")

        # If they create a new post and link directly to one and only one image it doesn't list in the subreddit, but it is in fact
        # embedded from another site. This happens.
        if len(element_link_set) == 0:
            find_element("//a[contains(@data-post-click-location, 'post-media-content')]", "href", "embedded image")

        # You can also directly embed the player from another site into Reddit via iframe from, say, RedGifs. This is what that video looks like.
        if len(element_link_set) == 0:
            iframes = self.elements_by_xpath
            find_element("//div[contains(@class, 'embeddedPlayer')]/video", "src", "iframe")

        if len(element_link_set) == 0:
            LOG.info("Did not find any media.")
            post.canonical_media_urls = "[NOMEDIA]"
            return False
        post.canonical_media_urls = ','.join(element_link_set.keys())
        return True

    def find_image(self, image, confidence=0.6, **kwargs):
        image_location = RedditNormalizeImageLocations.screenshot_targets_dir / image
        LOG.debug(f"Finding image {image_location}")
        # Recall that these are absolute (non-retina) coordinates.
        # Assume that dialog boxes are in the middle-ish of the screen
        non_retina_size = [c for c in pyautogui.size()]
        non_retina_bounding_box_radius=500
        region = [non_retina_size[0] - non_retina_bounding_box_radius,
                  non_retina_size[1] - non_retina_bounding_box_radius,
                  non_retina_bounding_box_radius * 2,
                  non_retina_bounding_box_radius * 2]
        LOG.trace(f"Locating image in bounding box of {region}")
        location = pyautogui.locateOnScreen(str(image_location), grayscale=False, confidence=confidence, region=region, **kwargs)
        if location == None:
            raise Exception(f"Couldn't find image; reference img {image_location}")
        center = pyautogui.center(location)
        retina_center = [c / 2 for c in center]
        LOG.info(f"Image found at (non-retina coords) {center}; retina coords {retina_center}")
        return retina_center

    def jiggle_click(self, coordinates):
        x = coordinates[0]
        y = coordinates[1]
        for i in range(3):
            jiggle_x = x + random.randint(-3, 3)
            jiggle_y = y + random.randint(-3, 3)
            pyautogui.moveTo((jiggle_x, jiggle_y))
            time.sleep(0.02)
        pyautogui.moveTo((x, y))
        pyautogui.click()

    def download_assets_if_not_present(self, post):
        '''
        This is to be called after the assets have been populated in the browser
        '''
        media_urls = post.canonical_media_urls
        if media_urls == None or media_urls == '':
            LOG.info("Media url is empty; skipping")
            return False
        for media_url in media_urls.split(','):
            # Check if it's on the filesystem
            concrete_media_dir_path = pathlib.Path(RedditNormalizeImageLocations.media_download_dir)
            if not concrete_media_dir_path.exists():
                concrete_media_dir_path.mkdir()
            server_path = urllib.parse.urlparse(media_url)
            filename = pathlib.Path(server_path.path).name
            destination_files = glob.glob(str(RedditNormalizeImageLocations.media_download_dir) + "/**/*" + pathlib.Path(filename).stem + "*", recursive=True)
            if len(destination_files) != 0:
                LOG.info(f"Local file for {filename} appears to already exist on the FS.")
            else:
                LOG.info(f"Local file for {filename} does not exist locally; we'll download it.")
                driver().get(media_url)
                time.sleep(0.2)
                current_url = driver().current_url
                if current_url.endswith("removed.png"):
                    LOG.info("Current image seems to be removed")
                    post.canonical_media_urls = "[DELETED]"
                    continue
                # Wait for page to fully load? Get an element with implicit wait? Does it do this anyway?
                LOG.info("Sending save hotkey")
                retries = 4
                # Latch this so we don't try to save multiple times
                found_save_image_somewhere = False
                for i in range(retries):
                    # Try to click the button first, then if it's not present, send the hotkey.
                    # This is because the hotkey will dismiss (with the correct action!) the dialog
                    # meaning it will disappear and we'll retry through all the retries for a
                    # dialog that is never there.
                    try:
                        pyautogui.hotkey('command', 's')
                        time.sleep(0.2)
                        retina_center = self.find_image("save_page.png", 0.7)
                        self.jiggle_click(retina_center)
                        break
                    except Exception as e:
                        LOG.debug(f"Did not find save button: try {i} of {retries}")
                for i in range(retries):
                    try:
                        retina_center = self.find_image("replace_existing_file.png", 0.95)
                        self.jiggle_click(retina_center)
                        # dont break, just keep retrying.
                    except Exception as e:
                        LOG.debug(f"Did not find replace prompt (this can be normal): try {i} of {retries} {e}")
                        pass
                # Allow the file to download; then move it
                time.sleep(2)
                files = glob.glob(str(pathlib.Path.home()) + "/Downloads/**/*" + pathlib.Path(filename).stem + "*", recursive=True)
                def move_file_to_media(file):
                    '''
                    Little helper
                    '''
                    dest = str(RedditNormalizeImageLocations.media_download_dir) + "/" + file.name
                    LOG.info(f"Moving {str(file)} to {dest}")
                    file.rename(dest)

                if len(files) != 1:
                    LOG.warning(f"Found 0 or more than one files in Downloads for {filename}; trying to find best match from {files}")
                    minimum_distance = 0.0
                    minimum_file = None
                    for f in files:
                        fpath = pathlib.Path(f)
                        if fpath.is_file():
                            # Do a difference. Sometimes the file might be hosted with a .gif extension and instead be .mp4
                            # on the filesystem, so we choose the closest of the filenames of the path.
                            ratio = difflib.SequenceMatcher(None, fpath.name, filename).ratio()
                            if ratio > minimum_distance:
                                LOG.debug(f"New closest match found: {fpath.name} to {filename} is {ratio}")
                                minimum_distance = ratio
                                minimum_file = fpath
                        else:
                            LOG.trace(f"{f} is not a file, maybe a dir?")
                    if minimum_file == None:
                        LOG.warning("No match found for file {filename}; assume it's broken / removed.")
                    else:
                        move_file_to_media(minimum_file)
                else:
                    file = pathlib.Path(files[0])
                    move_file_to_media(file)



    def execute(self):
        #filter(RedditImagePost.canonical_media_urls.is_(None)). \
        query = Storage.session().query(RedditImagePost). \
                filter(RedditImagePost.canonical_media_urls.is_not("[NOMEDIA]")). \
                limit(self._num_posts)
        if self._offset > 0:
            query = query.offset(self._offset)
        LOG.info(f"Processing results of query: {str(query)}")
        posts_to_process = query.all()
        for i in range(self._num_posts):
            if i + 1 >= len(posts_to_process):
                LOG.info("Ran out of posts, we must be done!")
                return True
            post = posts_to_process[i]
            LOG.debug(f"Raw image link for {post.path} is {post.image_url}")
            if not post.canonical_media_urls:
                if post.image_url == None:
                    self.handle_reddit_image_post(post)
                else:
                    url = urllib.parse.urlparse(post.image_url)
                    if "imgur" in url.netloc:
                        if pathlib.Path(url.path).suffix == '':
                            self.handle_imgur_page_before_image(post)
                        else:
                            self.handle_complete_imgur_link(post)
                    if hasattr(post, 'canonical_media_urls'):
                        LOG.info(f"Canonical media link is {post.canonical_media_urls}")
                    else:
                        LOG.info(f"Post has no canonical media; assuming it's dead.")
            else:
                LOG.info("Canonical URL is already populated; delete it to reprocess if needed.")
            # TODO: this no-ops if the assets are local; is that the cleanest place to do this?
            self.download_assets_if_not_present(post)
            # And save the model.
            Storage.session().commit()
        return True
