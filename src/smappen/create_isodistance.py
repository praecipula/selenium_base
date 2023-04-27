#!/usr/bin/env python3

# Create a Smappen isodistance from the current pin location at the given diameter.
# Can accept either km or mi

from base import driver, By, ASSERT, AutomationCommandBase, CommandParser

import time
import math
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from smappen import SmappenParamsPanel

import logging

LOG = logging.getLogger(__name__)

class SmappenCreateIsodistance(AutomationCommandBase):

    name = "smappen_create_isodistance"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("distance", metavar='DISTANCE', type=str) # A distance, like 5mi or 10km

    def find_new_isodistance_element(self, text):
        LOG.debug("Waiting for isodistance to be calculated...")
        driver().find_element(By.XPATH, "//*[@data-cy='area']//span[contains(text(), '" + text + "')]")
        LOG.debug("Found element")

    def execute(self):
        # Start closed just to be sure
        panel = SmappenParamsPanel()
        if panel.is_open():
            panel.close()

        # Add an area
        panel.create_area()
        panel.click_distance_area_type()
        panel.click_car_mode()
        panel.enter_distance_km(self._args.distance)
        panel.click_calculate()
        self.find_new_isodistance_element(str(self._args.distance + "km"))
        # This is here because after we find the distance, the drawer closes - and animates closed. Wait for it to close.
        time.sleep(1)
        return True
