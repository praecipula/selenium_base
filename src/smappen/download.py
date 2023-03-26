#!/usr/bin/env python3

# Create a Smappen isodistance from the current pin location at the given diameter.
# Can accept either km or mi

from base import driver, By, ASSERT, AutomationCommandBase, CommandParser

import time
import math
import smappen
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import logging

LOG = logging.getLogger(__name__)

class SmappenDownload(smappen.SmappenBase):

    name = "smappen_download"

    parser = CommandParser(prog = name, description=f'{name} command')


    def execute(self):
        # Start closed just to be sure
        panel = smappen.SmappenParamsPanel()
        if panel.is_open():
            panel.close()

        self._data_cy_click("mapMenu")
        self._data_cy_click("exportKml")
        return True
