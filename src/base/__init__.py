import logging.config
import yaml
import re
import os
 
## SELENIUM SETUP
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
# create webdriver object 
opts = Options()
opts.add_argument("--profile")
opts.add_argument(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ff_profile.selenium'))

global _driver
_driver = None
selenium_implicit_wait_default = 10
def driver():
    global _driver
    if not _driver:
        _driver = webdriver.Firefox(options=opts)         
        # set implicit wait time
        _driver.implicitly_wait(selenium_implicit_wait_default) # seconds
    return _driver

from selenium.webdriver.common.action_chains import ActionChains

## LOGGING SETUP
import python_logging_base
from python_logging_base import ASSERT

LOG = logging.getLogger("daily_start")
LOG.setLevel(logging.TRACE)

# BASE CLASSES AND FUNCTIONALITY
import argparse
class CommandParser(argparse.ArgumentParser):

    class ParseError(Exception):
        pass

    # TODO: bring this into an ASSERT when I'm sure that handles stack traces usefully.
    def error(self, message):
        LOG.critical(message)
        raise CommandParser.ParseError(message)

class AutomationCommandBase:
    name = "INHERITORS_SHOULD_OVERRIDE"

    parser = None
    #Override using argparse like this
    #parser = CommandParser(prog = name, description=f'{name} command')
    #parser.add_argument("uri", metavar='URI', type=str)


    def __init__(self, command_args):
        self._argstr = command_args
        self._args = self.__class__.parser.parse_args(command_args)
        self._results = {}
        
    def __str__(self):
        return f"{self.__class__.name}: {self._args}"

    @staticmethod
    def element_by_xpath(xpath, base_element=None):
        elements = AutomationCommandBase.elements_by_xpath(xpath, base_element)
        if elements == None:
            ASSERT(elements != None, f"Search for element with xpath {xpath} returned no results")
            return None
        if not ASSERT(len(elements) == 1, f"Found more than one element with xpath {xpath}; returning first"):
            return elements[0]
        return elements[0] #Should be the only one.

    @staticmethod
    def elements_by_xpath(xpath, base_element=None):
        elements = None
        if not base_element:
            elements = driver().find_elements(By.XPATH, xpath)
        else:
            elements = base_element.find_elements(By.XPATH, xpath)
        if len(elements) == 0:
            LOG.info("We didn't find any element")
            return None
        return elements

    @property
    def results(self):
        return self._results
