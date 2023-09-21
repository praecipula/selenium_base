import os
import time
import random
import pyautogui
import urllib.parse
import mouse_and_key.util as util
import glob
import pathlib

from base import driver, AutomationCommandBase, CommandParser
import selenium

import logging
import python_logging_base
from python_logging_base import ASSERT

LOG = logging.getLogger("wanik_vocab")
LOG.setLevel(logging.TRACE)

# Pillow is a little noisy by default, so let's up that one logger.
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)

class WanikaniGetVocab(AutomationCommandBase):
    name = "wanikanivocab"
    '''
    Given:
    Tab of Chrome that is open to a WaniKani vocab
    Get the vocab entries into Anki
    '''

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("uri", metavar='U', type=str, help = "A WaniKani vocab page to go to")
    parser.add_argument('-n', "--number", metavar='N', type=int, help = "A number of times / pages to scrape", default=1, required=False)

    wait_time = 5

    def set_level(self):
        # Get level from element:
        # <a class="page-header__icon page-header__icon--level" href="/level/2">2</a>
        self._level = self.element_by_xpath("//a[contains(@class, '--level')]").text
        LOG.info(f"Wanikani level: {self._level}")

    def set_meanings(self):
        # A div with class container...
        # section elements...
        # with a header somewhere in there, h2, whose value is "Primary" (this is the "key=" of a key value setup)...
        # following p siblings (the "value" of a key value setup)
        # its text.
        paragraphs = self.elements_by_xpath("//div[contains(@class, 'container')]//section[@id='section-meaning']//h2[text() = 'Primary']/parent::*/p")
        self._meaning = "\n".join([p.text for p in paragraphs])
        LOG.info(f"Meaning: {self._meaning}")
        # TODO: secondary meanings

    def set_anki_meaning(self, shortcut_image=False):
        LOG.info("Setting anki meaning")
        if shortcut_image:
            pyautogui.press('tab')
        else:
            retina_center = util.find_image("anki_meaning.png", 0.8)
            pyautogui.moveTo(retina_center[0], retina_center[1] + 35)
            pyautogui.click()
        util.write_text(self._meaning)
        # Used for an optimization (if we're tabbing through fields we can look for the mouse to guess
        # that we can just tab for the next field instead of searching for an image

    def set_meaning_explanation(self):
        paragraphs = self._meaning_explanation = self.elements_by_xpath("//div[contains(@class, 'container')]//section[@id='section-meaning']//h3[text() = 'Explanation']/parent::*/p")
        self._meaning_explanation = "\n".join([p.text for p in paragraphs])
        LOG.info(f"Meaning explanation: {self._meaning_explanation}")
        # TODO: secondary meanings?

    def set_anki_meaning_explanation(self, shortcut_image=False):
        LOG.info("Setting anki meaning explanation")
        if shortcut_image:
            pyautogui.press('tab')
        else:
            retina_center = util.find_image("anki_meaning_explanation.png", 0.8)
            pyautogui.moveTo(retina_center[0], retina_center[1] + 35)
            pyautogui.click()
        util.set_clipboard(self._meaning_explanation)
        util.paste()

    def set_word_types(self):
        paragraphs = self._word_type =  self.elements_by_xpath("//div[contains(@class, 'container')]/section//h2[text() = 'Word Type']/parent::*/p")
        self._word_type = "\n".join([p.text for p in paragraphs])
        LOG.info(f"Word type: {self._word_type}")
        #TODO: secondary word types?

    def set_anki_word_types(self, shortcut_image=False):
        LOG.info("Setting anki word types")
        if shortcut_image:
            pyautogui.press('tab')
        else:
            retina_center = util.find_image("anki_word_type.png", 0.8)
            pyautogui.moveTo(retina_center[0], retina_center[1] + 35)
            pyautogui.click()
        util.set_clipboard(self._word_type)
        util.paste()

    def set_readings(self):
        self._readings = {}
        readings_groups = self.elements_by_xpath("//div[@class='reading-with-audio']")
        for group in readings_groups:
            japanese_reading = self.element_by_xpath("./div[@lang='ja']", group).text
            self._readings[japanese_reading] = []
            audio_tags = self.elements_by_xpath(".//audio/source[@content_type='audio/mpeg']", group)
            for element in audio_tags:
                # This blocks because Firefox doesn't even load anything with direct download and Selenium waits.
                # Aggravating.
                # Kill it with timeout.
                old_timeout = driver().timeouts.page_load
                try:
                    # This does in fact need to be long enough to resolve and download.
                    # This is because we're going to use the last downloaded file to get the
                    # "real" filename to give to Anki, since we've sort of lost track of how
                    # to get this filename.
                    driver().set_page_load_timeout(1)
                    audio_source = driver().get(element.get_attribute("src"))
                except selenium.common.exceptions.TimeoutException:
                    # Expected!
                    pass
                driver().set_page_load_timeout(old_timeout)
                # OK, now get the filename.
                list_of_files = glob.glob(os.path.expanduser('~/Downloads/*.mp3')) # * means all if need specific format then *.csv
                latest_filename = max(list_of_files, key=os.path.getctime)
                latest_file = pathlib.Path(latest_filename)
                LOG.info(f"Downloaded {latest_file}")
                # Now move the file
                anki_media_dir = pathlib.Path(os.path.expanduser('~/Library/Application Support/Anki2/User 1/collection.media'))
                destination_file = anki_media_dir / latest_file.name
                LOG.info(f"Moving to {destination_file}")
                os.replace(latest_file.resolve(), destination_file.resolve())
                self._readings[japanese_reading].append(destination_file)
        LOG.info(f"Got readings {self._readings}")

    def set_anki_readings(self, shortcut_image=False):
        LOG.info("Setting anki readings")
        if shortcut_image:
            pyautogui.press('tab')
        else:
            retina_center = util.find_image("anki_kana.png", 0.8)
            pyautogui.moveTo(retina_center[0], retina_center[1] + 35)
            pyautogui.click()
        for (kana, audio_files) in self._readings.items():
            # Annoyingly, pyautogui dies on writing non-english characters. So we'll use the clipboard.
            util.set_clipboard(kana)
            util.paste()
            for audio in audio_files:
                util.set_clipboard(f"[sound:{audio.name}]")
                util.paste()

    def set_reading_explanation(self):
        paragraphs = self.elements_by_xpath("//div[contains(@class, 'container')]//section[@id='section-reading']//h3[text() = 'Explanation']/parent::*/p")
        if paragraphs == None:
            self._readings_explanation = "!!![NO WANIKANI FIELD FOUND]!!!"
            LOG.error("Could not find reading explanation for {self._vocab}")
            return
        self._readings_explanation = "\n".join([p.text for p in paragraphs])
        LOG.info(f"Reading explanation: {self._readings_explanation}")
        # TODO: secondary meanings?

    def set_anki_reading_explanation(self, shortcut_image=False):
        LOG.info("Setting anki reading explanation")
        if shortcut_image:
            pyautogui.press('tab')
        else:
            retina_center = util.find_image("anki_reading_explanation.png", 0.93)
            pyautogui.moveTo(retina_center[0], retina_center[1] + 35)
            pyautogui.click()
        util.set_clipboard(self._readings_explanation)
        util.paste()


    def new_anki_card(self):
        util.activate_dock_app_by_image("anki_in_dock.png")
        retina_center = util.find_image("new_anki_card.png", 0.8)
        util.jiggle(retina_center)
        pyautogui.click()
        # Takes a second I guess
        time.sleep(1)
        # Scroll back up in case we forgot
        util.center_mouse()
        pyautogui.move(100, 0)
        util.jiggle()
        pyautogui.scroll(10)
        self.set_anki_vocab()
        self.set_anki_word_types(True)
        self.set_anki_meaning(True)
        self.set_anki_meaning_explanation(True)
        pyautogui.scroll(-10)
        self.set_anki_readings(True)
        self.set_anki_reading_explanation(True)
        pyautogui.scroll(-10)
        self.set_anki_tags()

    def set_anki_vocab(self):
        retina_center = util.find_image("anki_kanji_vocab.png", 0.8)
        pyautogui.moveTo(retina_center[0], retina_center[1] + 35)
        pyautogui.click()
        # Annoyingly, pyautogui dies on writing non-english characters. So we'll use the clipboard.
        util.set_clipboard(self._vocab)
        util.paste()

    def set_anki_tags(self):
        retina_center = None
        try:
            retina_center = util.find_image("anki_tags.png", 0.8)
        except util.ImageNotFoundException:
            # Swallow it once
            LOG.warn("Didn't find 0 tags header image. Trying with 2 tags.")
            pass
        if not retina_center:
            # Don't catch this one
            retina_center = util.find_image("anki_2_tags.png", 0.8)

        pyautogui.moveTo(retina_center[0]+ 500, retina_center[1] + 35)
        pyautogui.click()
        pyautogui.press('backspace', 30)
        util.write_text("Japanese")
        time.sleep(0.1)
        pyautogui.press('enter')
        util.write_text(f"WaniKani_L{self._level}")
        time.sleep(0.1)
        pyautogui.press('enter')

    def set_next_link(self):
        next_link = self.element_by_xpath("//nav[contains(@class, 'subject-pager')]//li[contains(@class, 'item--next')]//a").get_attribute('href')
        # It's so annoying to have the command line have the whole url, which we have to backspace over,
        # just to immediately strip the url on this script. So why not strip it first?
        self._next_vocab = urllib.parse.unquote(next_link.replace("https://www.wanikani.com/vocabulary/", ""))
        LOG.info(f"Next vocab: {self._next_vocab}")

    def populate_clipboard_with_next_link(self):
        next_command = f"kf; src/webby.py {WanikaniGetVocab.name} {self._next_vocab}"
        util.set_clipboard(next_command)
        LOG.info(f"Copied next command {next_command} to clipboard")

    def get_vocab_from_command_line(self, norm_uri):
        normalized_uri = urllib.parse.unquote(self._args.uri)
        if normalized_uri.startswith("https://www.wanikani.com/vocabulary/"):
            self._vocab = normalized_uri.replace("https://www.wanikani.com/vocabulary/", "")
        else:
            self._vocab = norm_uri
        LOG.info(f"Vocabulary from url: {self._vocab}")

    def get_radicals_used(self):
        mnemoic_and_radicals = self.elements_by_xpath("//div[contains(@class, 'container')]//section[@id='section-meaning']//h3[text() = 'Mnemonic']/parent::*/p")
        self._radicals = "\n".join([p.text for p in mnemoic_and_radicals])
        LOG.info(f"Set mnemonic / radicals to {self._radicals}")

    def get_onyomi(self):
        self._onyomi = self.element_by_xpath("//div[contains(@class, 'container')]//section[@id='section-reading']//h3[text() = 'On’yomi']/parent::*/p").text
        if self._onyomi == "None":
            self._onyomi = None
        LOG.info(f"Set onyomi to {self._onyomi}")

    def get_kunyomi(self):
        self._kunyomi = self.element_by_xpath("//div[contains(@class, 'container')]//section[@id='section-reading']//h3[text() = 'Kun’yomi']/parent::*/p").text
        if self._kunyomi == "None":
            self._kunyomi = None
        LOG.info(f"Set kunyomi to {self._kunyomi}")

    def get_nanori(self):
        self._nanori = self.element_by_xpath("//div[contains(@class, 'container')]//section[@id='section-reading']//h3[text() = 'Nanori']/parent::*/p").text
        if self._nanori == "None":
            self._nanori = None
        LOG.info(f"Set nanori to {self._nanori}")

    def hack_edit_kanji(self):
        # Assume: lots of stuff 
        # Anki browse is full screen
        # We already have a card (just not the kanji)
        # Screen resolution for hardcoding, etc...
        util.activate_dock_app_by_image("anki_in_dock.png")
#        # Search
#        util.jiggle((661, 72))
#        pyautogui.click()
#        pyautogui.press('backspace', 50)
#        util.set_clipboard(self._vocab)
#        util.paste()
#        pyautogui.press('enter')
#        #Select first element
#        util.jiggle((273,126))
#        pyautogui.click()
        # Go to right pane and scroll all the way down
        util.jiggle((1309,215))
        pyautogui.scroll(-500)
        # Get the radicals used field activated
        retina_center = util.find_image("anki_radicals_used.png", 0.8)
        pyautogui.moveTo(retina_center[0], retina_center[1] + 35)
        pyautogui.click()
        util.set_clipboard(self._radicals)
        util.paste()
        # Tab through onyomi, kunyomi, nanori
        pyautogui.press('tab')
        # Paste the onyomi
        if self._onyomi != None:
            util.set_clipboard(self._onyomi)
            util.paste()
        # Tab through kunyomi, nanori
        pyautogui.press('tab')
        if self._kunyomi != None:
            util.set_clipboard(self._kunyomi)
            util.paste()
        pyautogui.press('tab')
        if self._nanori != None:
            util.set_clipboard(self._nanori)
            util.paste()

    def get_word_or_phrase(self):
        LOG.info(f"Getting vocabulary word: {self._vocab}")
        driver().get(f"https://www.wanikani.com/vocabulary/{self._vocab}")
        self.set_level()
        # Go ahead and populate main sections
        self.set_meanings()
        self.set_meaning_explanation()
        self.set_word_types()
        self.set_readings()
        self.set_reading_explanation()

        self.new_anki_card()
        self.set_next_link()

    def get_kanji(self):
        # Do more work for single characters (standalone Kanji)
        if len(self._vocab) == 1:
            LOG.info("f{self._vocab} also seems to be a standalone kanji; getting pronunciations")
            driver().get(f"https://www.wanikani.com/kanji/{self._vocab}")
            self.get_radicals_used()
            self.get_onyomi()
            self.get_kunyomi()
            self.get_nanori()
            self.hack_edit_kanji()
        else:
            LOG.info("Not a single character, skipping kanji info")


        # Swell! Now populate Anki with the good old mouse and key.

    def countdown_and_add_to_anki(self):
        countdown_seconds = 10
        for i in range(countdown_seconds):
            LOG.info(f"Adding in {countdown_seconds - i} seconds...")
            time.sleep(1)
        retina_center = util.find_image("anki_add_button.png", 0.8)
        pyautogui.moveTo(retina_center[0], retina_center[1] )
        pyautogui.click()

    def execute(self):
        normalized_uri = urllib.parse.unquote(self._args.uri)
        # Loop
        for i in range(self._args.number):
            LOG.info(f"Getting vocab {i} of {self._args.number}")
            if hasattr(self, "_next_vocab"):
                self._vocab = self._next_vocab
            else:
                self.get_vocab_from_command_line(normalized_uri)
            self.get_word_or_phrase()
            self.get_kanji()
            self.populate_clipboard_with_next_link()
            self.countdown_and_add_to_anki()
        return True

