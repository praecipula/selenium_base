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

class CrunchbaseSearch(AutomationCommandBase):
    name = "cbasesearch"
    '''
    Given:
    '''

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("--uri", metavar='U', type=str, help = "A Crunchbase saved search uri", required=False)

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
    def local_path(uri):
        hex_search_nonce = uri.split('/')[-1]
        filename = f"cb_search_{hex_search_nonce}"
        path = pathlib.Path(f"/Users/matt/Downloads/{filename}.html")
        return path

    def load_search_page(self, uri):
        LOG.info(f"Loading search page at {uri}")
        util.activate_dock_app_by_image("chrome_in_dock.png")
        self.new_tab(f"{uri}")
        time.sleep(6)
        # We have to work with the undetected driver here.
        # The first argument only has to be set to True once (the driver is global and cached on create)
        LOG.todo(f"Pagination?")

    def save_search_page(self, uri = None):
        util.activate_dock_app_by_image("chrome_in_dock.png")
        if uri == None:
            LOG.info("Getting current Chrome tab uri as the correct uri")
            with pyautogui.hold('command'):
                pyautogui.press('l')
                pyautogui.press('c')
            uri = util.get_clipboard().decode('utf-8')
            LOG.info(f"Inferred URI: {uri}")
        with pyautogui.hold('command'):
            pyautogui.press('s')
        time.sleep(2)
        util.write_text(type(self).local_path(uri).stem)
        pyautogui.press("enter")
        time.sleep(6)
        return uri

    def get_headers(self):
        hd = self.elements_by_xpath("//sheet-grid//grid-column-header")
        self._headers = [e.text for e in hd][1:-1]
        # Something like
        # ['', 'Organization Name', 'Last Funding Type', 'IPO Status', 'Industries', 'Headquarters Location', 'Description', 'CB Rank (Company)', 'Founded Date', 'Number of Investments', 'Number of Exits', 'Industry Groups', 'Founders', 'Number of Employees', 'Diversity Spotlight (US Headquarters Only)', 'ADD COLUMN']
        LOG.debug(f"Got headers: {self._headers}")
        return self._headers

    def get_rows(self):
        self._rows = self.elements_by_xpath("//sheet-grid//grid-row")
        LOG.debug(f"Found {len(self._rows)} rows")
        self._row_dictionaries = []
        for row_idx, row in enumerate(self._rows):
            dct = {}
            cells = self.elements_by_xpath("./grid-cell", row)
            for idx, cell in enumerate(cells[1:-1]):
                dct[self._headers[idx]] = cell.text
            self._row_dictionaries.append(dct)
            LOG.info(f"Row {row_idx} of {len(self._rows)} complete")
            LOG.trace(f"Parsed: {dct}")

    def create_spreadsheet_data(self, url_path):
        page_number_regex = r'pageId=(\d+)'
        matches = re.search(page_number_regex, url_path)
        pagenum = 1
        if matches is not None:
            pagenum = matches.groups()[0]
        path = pathlib.Path(__file__).with_name(f"crunchbase_p{pagenum}.csv")
        with open(path.resolve(), 'w', newline='') as csvfile:
            fieldnames = self._headers
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in self._row_dictionaries:
                writer.writerow(row)
        # Translate the raw data to a dictionary form.
        # This is also where we might want to do any Python preprocessing.

    def cb_next_page(self):
        util.activate_dock_app_by_image("chrome_in_dock.png")
        retina_center = util.find_image("cb_next_link.png")
        util.jiggle(retina_center)
        pyautogui.click()
        util.activate_dock_app_by_image("iterm_in_dock.png")
        delay = 10
        for i in range(delay):
            LOG.info(f"Continuing in {delay - i} seconds...")
            time.sleep(1)
        util.write_text("cb")
        pyautogui.press('enter')


#    def switch_to_spreadsheet_window(self):
#        util.activate_dock_app_by_image("chrome_in_dock.png")
#        # Other window needs activation
#        with pyautogui.hold('command'):
#            pyautogui.press('~')
#        # Select import from the file menu
#        retina_center = util.find_image("sheets_file_menu.png")
#        util.jiggle(retina_center)
#        pyautogui.click()
#        pyautogui.press('down', 3)
#        pyautogui.press('enter')
#        time.sleep(2)
#        # Select the upload from computer tab
#        retina_center = util.find_image("sheets_upload_tab.png")
#        util.jiggle(retina_center)
#        pyautogui.click()
#        time.sleep(1)
#        retina_center = util.find_image("sheets_file_browse.png")
#        util.jiggle(retina_center)
#        pyautogui.click()
#        time.sleep(1) #Select and upload time
#        # Select the most recent file
#        pyautogui.press('down')
#        pyautogui.press('enter')
#        time.sleep(8) #Select and upload time
#        # Import as a new sheet, not a new whole spreadsheet
#        retina_center = util.find_image("sheets_import_location.png")
#        util.jiggle(retina_center)
#        pyautogui.click()
#        pyautogui.press('down')
#        pyautogui.press('enter')

    def execute(self):
        """
        Gonna have to do this the "hard way"; save the complete page with a mouse-and-key approach, then open
        the page with Selenium to do xpath finding, etc...
        """
        if self._args.uri != None:
            normalized_uri = urllib.parse.unquote(self._args.uri)
            self.load_search_page(normalized_uri)
            self.save_search_page(normalized_uri)
        else:
            normalized_uri = self.save_search_page(None)
        # Have to urlencode the question mark
        unencoded_path = str(type(self).local_path(normalized_uri))
        quoted = urllib.parse.quote(unencoded_path)
        LOG.info("Beginning parse...")
        driver().get(f"file://" + quoted)
        self.get_headers()
        self.get_rows()
        self.create_spreadsheet_data(unencoded_path)
        self.cb_next_page()
        return True

