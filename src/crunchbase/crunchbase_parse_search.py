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


from base import driver, AutomationCommandBase, CommandParser, selenium_implicit_wait_default

import logging
import python_logging_base
from python_logging_base import ASSERT

LOG = logging.getLogger("cbase_parse")
LOG.setLevel(logging.DEBUG)

# We don't need such verbosity on the base parser for e.g. finding or not xpath elements
logging.getLogger("base").setLevel(logging.INFO)

class CrunchbaseParseSearch(AutomationCommandBase):
    name = "cbaseparse"
    '''
    Given:
    '''

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("--file", metavar='F', type=str, help = "A particular file to parse (default: all html files)", required=False)
    parser.add_argument("--overwrite", help = "Whether to overwrite output files", required=False, action='store_true')

    wait_time = 5
    link_target_regex = r'href=\"(?P<link>.*?)\"'

    def get_headers(self):
        hd = self.elements_by_xpath("//sheet-grid//grid-column-header")
        self._headers = [e.text for e in hd][1:-1]
        # Something like
        # ['', 'Organization Name', 'Last Funding Type', 'IPO Status', 'Industries', 'Headquarters Location', 'Description', 'CB Rank (Company)', 'Founded Date', 'Number of Investments', 'Number of Exits', 'Industry Groups', 'Founders', 'Number of Employees', 'Diversity Spotlight (US Headquarters Only)', 'ADD COLUMN']
        LOG.debug(f"Got headers: {self._headers}")
        return self._headers

    def get_rows(self):
        # We know that the search should be very fast = this is a file on the fs.
        # So we'll do the whole thing with tiny timeout, since we know there will be some
        # non-matching columns we want to eagerly fail on.
        driver().implicitly_wait(0.01)
        self._rows = self.elements_by_xpath("//sheet-grid//grid-row")
        LOG.debug(f"Found {len(self._rows)} rows")
        self._row_dictionaries = []
        for row_idx, row in enumerate(self._rows):
            dct = {}
            cells = self.elements_by_xpath("./grid-cell", row)
            for idx, cell in enumerate(cells[1:-1]):
                dct[self._headers[idx]] = cell.text
                flat_html = cell.get_attribute('innerHTML')
                if flat_html.find("<a") != -1:
                    # We just might have an anchor link. Do a real search.
                    inner_links = self.elements_by_xpath(".//a", cell)
                    if inner_links != None and len(inner_links) > 0:
                        # Append to the headers if links breakout isn't present, not interrupting the indexing of the
                        # headers by position. 
                        link_header = self._headers[idx] + " [Links]"
                        if not link_header in self._headers:
                            self._headers.append(link_header)
                        dct[link_header] = ", ".join([l.get_attribute("href") for l in inner_links])
            self._row_dictionaries.append(dct)
            LOG.info(f"Row {row_idx} of {len(self._rows)} complete")
            LOG.trace(f"Parsed: {dct}")
        driver().implicitly_wait(selenium_implicit_wait_default)



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

    def parse(self):
        files = glob.glob(os.path.dirname(__file__) + "/**/**/*.html")

        for idx, file in enumerate(files):
            self.parse_one_file(pathlib.Path(file))
            LOG.info(f"{idx} of {len(files)} complete.")
    
    def parse_one_file(self, filepath):
        working_dir = filepath.parent
        html_stem = filepath.stem
        regex = r"pageId=(\d+)"
        pagenum = 1
        match = re.search(regex, html_stem)
        if match != None:
            pagenum = int(match[1])
        output_file = working_dir / f"crunchbase_p{pagenum}_v2.csv"
        if output_file.exists() and self._args.overwrite == False:
            LOG.info("Not parsing: output file exists")
            return True
        LOG.info(f"Beginning parse from {filepath} to {output_file.name}...")
        driver().get(f"file://" + urllib.parse.quote(str(filepath)))
        self.get_headers()
        self.get_rows()
        self.create_spreadsheet_data(output_file)
        LOG.info(f"{html_stem} complete!")

    def create_spreadsheet_data(self, csvfile_path):
        with open(csvfile_path.resolve(), 'w', newline='') as csvfile:
            fieldnames = self._headers
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in self._row_dictionaries:
                writer.writerow(row)
        # Translate the raw data to a dictionary form.
        # This is also where we might want to do any Python preprocessing.


    def execute(self):
        """
        Gonna have to do this the "hard way"; save the complete page with a mouse-and-key approach, then open
        the page with Selenium to do xpath finding, etc...
        """
        self.parse()
        return True

#        if self._args.uri != None:
#            normalized_uri = urllib.parse.unquote(self._args.uri)
#            self.load_search_page(normalized_uri)
#            self.save_search_page(normalized_uri)
#        else:
#            normalized_uri = self.save_search_page(None)
#        # Have to urlencode the question mark
#        unencoded_path = str(type(self).local_path(normalized_uri))
#        quoted = urllib.parse.quote(unencoded_path)
#        LOG.info("Beginning parse...")
#        driver().get(f"file://" + quoted)
#        self.get_headers()
#        self.get_rows()
#        self.create_spreadsheet_data(unencoded_path)
#        self.cb_next_page()
#        return True
#
