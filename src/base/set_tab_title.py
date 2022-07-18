#!/usr/bin/env python3

# Set the title of the tab. Quick and easy place for feedback.

from base import driver, By, ASSERT, AutomationCommandBase, CommandParser

import time
import math
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from smappen import SmappenParamsPanel

import logging

LOG = logging.getLogger(__name__)

class SetTabTitle(AutomationCommandBase):

    name = "set_tab_title"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("text", metavar='TEXT', type=str) # A distance, like 5mi or 10km


    def execute(self):
        # TODO: in a multi-tab environment we might need to think about which tab is active.
        # I think it's reasonable to require the scripter to select the tab then this sets the
        # title of the active tab.
        driver.execute_script('document.title = "' + self._args.text + '"')
        return True
