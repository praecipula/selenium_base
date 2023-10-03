import os
import time
import random
import pyautogui
import urllib.parse
import mouse_and_key.util as util
import glob
import re
import pathlib
import csv


from base import driver, AutomationCommandBase, CommandParser

import logging
import python_logging_base
from python_logging_base import ASSERT

LOG = logging.getLogger("cbase_search")
LOG.setLevel(logging.DEBUG)

# Pillow is a little noisy by default, so let's up that one logger.
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)

class CrunchbaseCompanyProfile(AutomationCommandBase):
    name = "cbaseprofile"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("--link", metavar='N', type=str, help = "A Crunchbase org link", required=False)
    parser.add_argument("--file", metavar='F', type=str, help = "A filename for list of names", required=False)

    wait_time = 5

    @staticmethod
    def new_tab(address):
        LOG.info(f"Opening tab at {address}")
        with pyautogui.hold('command'):
            pyautogui.press('t')
        time.sleep(0.25)
        util.write_text(address)
        pyautogui.press("enter")

    @staticmethod
    def navigate_to(address):
        LOG.info(f"Navigating to {address}")
        with pyautogui.hold('command'):
            pyautogui.press('l')
        time.sleep(0.1)
        pyautogui.press('backspace')
        util.set_clipboard(address)
        util.paste()
        time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(0.1)

    @staticmethod
    def activate_tab(tab_no):
        with pyautogui.hold('command'):
            pyautogui.press(str(tab_no))

    @staticmethod
    def company_name_from_uri(uri):
        split = uri.split('/')
        # ['https:', '', 'www.crunchbase.com', 'organization', 'openai', 'company_financials']
        return split[4]

    @staticmethod
    def local_path(uri):
        company_name = CrunchbaseCompanyProfile.company_name_from_uri(uri)
        split = uri.split('/')
        if len(split) > 5:
            sub_tab = split[5]
            filename = f"cb_company_{company_name}_{sub_tab}"
        else:
            filename = f"cb_company_{company_name}"
        path = pathlib.Path(f"/Users/matt/Downloads/{filename}.html")
        return path

    def load_company_page(self, link):
        LOG.info(f"Loading company page for {link}")
        util.activate_dock_app_by_image("chrome_in_dock.png")
        self.activate_tab(1)
        self.navigate_to(link)
        time.sleep(0.5)

    def save_current_page(self):
        # Saves whatever page we're currently on
        LOG.info("Getting current Chrome tab uri as the company page")
        with pyautogui.hold('command'):
            pyautogui.press('l')
            pyautogui.press('c')
        uri = util.get_clipboard().decode('utf-8')
        LOG.info(f"Inferred URI: {uri}")
        
        # Check if exists so we don't need to redownload
        file_path = self.local_path(uri)
        if file_path.exists():
            LOG.info("File exists {file_path}; skipping save")
            return uri

        with pyautogui.hold('command'):
            pyautogui.press('s')
        time.sleep(0.3)
        util.set_clipboard(type(self).local_path(uri).stem)
        util.paste()
        pyautogui.press("enter")
        # Check if there is an overwrite prompt and say no
        # Also there's no need to sleep in this case so just early return
        try:
            time.sleep(0.3)
            retina_center = util.find_image("chrome_cancel_save.png", 0.8)
            util.jiggle(retina_center)
            pyautogui.click()
            LOG.debug("Not overwriting existing save on fs.")
            pyautogui.press('esc')
            return uri
        except util.ImageNotFoundException:
            LOG.debug("No overwrite box found; this is normal. Continuing to wait for download")
            # Also dismiss download box
            time.sleep(0.1)
            pyautogui.press('esc')
        return uri

    def save_company_tabs(self):
        # Start, we assume, at the current page.
        util.activate_dock_app_by_image("chrome_in_dock.png")
        self.activate_tab(1)
        LOG.info("Getting current Chrome tab uri as the company page")
        with pyautogui.hold('command'):
            pyautogui.press('l')
            pyautogui.press('c')
        uri = util.get_clipboard().decode('utf-8')
        LOG.info(f"Loaded URI: {uri}")
        # Since this page is the "fallback" one, go ahead and save it
        # so future fs checks will find it.
        self.save_current_page()
        # OK, now save one of each tab.
        self.activate_tab(2)
        self.navigate_to(f"{uri}/investor_financials")
        self.activate_tab(3)
        self.navigate_to(f"{uri}/company_financials")
        self.activate_tab(4)
        self.navigate_to(f"{uri}/recent_investments")
        self.activate_tab(5)
        self.navigate_to(f"{uri}/people")
        self.activate_tab(6)
        self.navigate_to(f"{uri}/technology")
        self.activate_tab(7)
        self.navigate_to(f"{uri}/signals_and_news")
        for i in range(2, 8):
            self.activate_tab(i)
            self.save_current_page()
    
        # Give time after all saves have been issued to download
        time.sleep(1)
        LOG.info("Collecting downloaded files")
        cname = self.company_name_from_uri(uri)
        pattern = f"/Users/matt/Downloads/*{cname}*"
        files = [pathlib.Path(f) for f in glob.glob(pattern)]
        subdir = pathlib.Path(f"/Users/matt/Downloads/{cname}")
        subdir.mkdir(exist_ok=True)
        for file in files:
            file.rename(subdir.resolve() / file.name)
        LOG.info(f"{uri} finished!")

    def execute(self):
        """
        Gonna have to do this the "hard way"; save the complete page with a mouse-and-key approach, then open
        the page with Selenium to do xpath finding, etc...
        """
        if self._args.link != None:
            normalized_link = urllib.parse.unquote(self._args.link)
            LOG.info("Processing {normalized_link}")
            self.load_company_page(normalized_link)
            # OK, that's the root page.
            # Now have to pull down and save the pages for each tab.
            self.save_company_tabs()
        if self._args.file != None:
            with open(self._args.file) as file:
                link_lines = file.readlines()
            for link in link_lines:
                normalized_link = urllib.parse.unquote(link)
                LOG.info("Processing {normalized_link}")
                self.load_company_page(normalized_link)
                self.save_company_tabs()

        return True

