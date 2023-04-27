from base import driver, By, Keys, ActionChains, AutomationCommandBase, CommandParser, ASSERT
from base.repl import drop_into_repl
import logging
import argparse
import os
import usaddress
import enchant
import time

LOG = logging.getLogger(__name__)

class SmappenBase(AutomationCommandBase):
    def _data_cy_click(self, attr_value):
        chain = ActionChains(driver())
        button_xpath = "//*[@data-cy='" + attr_value + "']"
        button = AutomationCommandBase.element_by_xpath(button_xpath)
        driver().execute_script("arguments[0].scrollIntoView(true);", button);
        chain.click(on_element=button)
        chain.perform()
        return True


class SmappenParamsPanel(SmappenBase):
    element_css = ".create-area-panel"

    def __init__(self):
        elements = driver().find_elements(By.CSS_SELECTOR, self.__class__.element_css)
        if len(elements) != 1:
            LOG.critical("Got more or less than 1 panel")
            exit(-1)
        self._panel = elements[0]

    def is_open(self):
        if self._panel.get_attribute("class").find("open") > -1:
            return True
        return False


    def create_area(self):
        LOG.debug("Creating new area")
        rv = self._data_cy_click("add-area")
        time.sleep(1)
        return rv

    def close(self):
        LOG.debug("Closing area creation panel")
        rv = self._data_cy_click("close-create-area-panel")
        time.sleep(1)
        return rv

    def click_distance_area_type(self):
        LOG.debug("Selecting distance area type")
        return self._data_cy_click("isodistance-button")

    def click_car_mode(self):
        LOG.debug("Selecting car mode for travel")
        return self._data_cy_click("car-button")

    def click_calculate(self):
        LOG.debug("Calculating...")
        return self._data_cy_click("iso-compute-button")

    def enter_distance_km(self, distance):
        LOG.debug(f"Entering distance of {distance} km")
        chain = ActionChains(driver())
        distance_textbox_xpath = "//input[@data-cy='input-range']"
        element = AutomationCommandBase.element_by_xpath(distance_textbox_xpath)
        element.clear()
        chain.send_keys_to_element(element, distance)
        chain.perform()

class SmappenMyMapPanel:

    @staticmethod
    def set_map_name(name):
        # Rename the map in Smappen to the address
        chain = ActionChains(driver())
        xpath = "//*[@data-cy='map-name']"
        element = AutomationCommandBase.element_by_xpath(xpath)
        chain.click(on_element = element)
        chain.click(on_element = element)
        chain.perform()
        subelement = driver().find_element(By.XPATH, xpath + "//input")
        chain.send_keys_to_element(subelement, Keys.BACKSPACE)
        chain.send_keys_to_element(subelement, name)
        chain.perform()
        return True


class SmappenEnsureLogin(AutomationCommandBase):
    """
    Setting a precedent.

    We are aiming for the DSL to be as "flat" as possible and aim for the flat commands to accept arguments
    that can adjust their behavior.

    This can lead to long commands, but we're looking for repetitive scripting here. Amortize the cost of the getting spelling right into the benefit it provides.

    This might be an opinion we change and make a BNF-DSL or something but I'm still aiming for command-line usage backed by programmatic actions. We call things with a somewhat obscure but still human-centered command, and the business logic can be done in Python for lower-level complexities.

    Finally, side effects ARE allowed, that is, a login action like this one can require the user to be on the home page before moving forward, requiring a navigation call before this one. We SHOULD limit this to tabs (so multiple threads => multiple tabs). This means that we might need something like a "tab session" where we explicitly identify a transaction that all is linear / has clean side effects boundaries.

    """
    name = "smappen_ensure_login"
    base_url = "https://smappen.com/app"
    login_url = "https://www.smappen.com/app/login"

    parser = CommandParser(prog = name, description=f'{name} command')

    def execute(self):
        LOG.info("Checking for login... ")
        # Go to the root page
        # Check to see if the page lists our profile
        if driver().current_url != SmappenEnsureLogin.base_url:
            driver().get(SmappenEnsureLogin.base_url)


        login_button_xpath = "//*[@data-cy='desktop-navbar-login-button']"
        elements = self.elements_by_xpath(login_button_xpath)
        # It's a pure search:
        # If we can find any elements that fit the pattern we are not logged in.
        # If we cannot find any elements then we *are* logged in
        # We make the choice simply based on existence.
        if elements == None:
            LOG.info("Could not find element, we think we're logged in already.")
            LOG.trace("TODO: implement a real non-null check to verify we are logged in.")
            return True
        LOG.info(f"Successfully detected we are not logged in")
        driver().get(SmappenEnsureLogin.login_url)
        # Prefer action chains - they will generally be human-ish enough to get the job done even
        # for times we need onBlur or onMouseMove
        chain = ActionChains(driver())
        LOG.trace("Entering in email address")
        username_xpath = "//input[@type='email']"
        element = self.element_by_xpath(username_xpath)
        chain.click(on_element=element)
        chain.send_keys_to_element(element, "dropclic@gmail.com")
        chain.perform()
        LOG.trace("Entering in password")
        password_xpath = "//input[@type='password']"
        element = self.element_by_xpath(password_xpath)
        chain.click(on_element=element)
        chain.send_keys_to_element(element, os.environ.get('SMAPPEN_PASSWORD'))
        chain.perform()
        LOG.trace("Submitting login")
        login_button_xpath = "//button[@type='submit']"
        element = self.element_by_xpath(login_button_xpath)
        chain.click(on_element=element)
        chain.perform()
        return True

    def __str__(self):
        return f"{self.__class__.name}: {self._args}"

class SmappenSearchForLocation(AutomationCommandBase):
    
    name = "smappen_search_for_location"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("address", metavar='ADDRESS', type=str)

    def execute(self):
        panel = SmappenParamsPanel()
        if panel.is_open():
            LOG.debug("Panel is open")
            panel.close()
        else:
            LOG.debug("Panel is closed")
            # Do nothing
        # Normalize the address by parsing and reemitting it in a standard format
        # TODO: this code will only work for this use case. It's going to likely need something
        # significantly more robust.
        # Find the search address bar and enter in the address
        LOG.trace("Entering in address")
        chain = ActionChains(driver())
        xpath = "//*[@id='search-address-bar']//input[@type='text']"
        element = self.element_by_xpath(xpath)
        chain.click(on_element=element)
        chain.send_keys_to_element(element, self._args.address)
        chain.perform()
        # Choose the first result. TODO: evaluate match quality vs. input; sometimes the OpenStreetMap results don't find the thing.
        # Example is the address "623 Fairmount Ave"; it can't find the street number, so zooms out to the next closest match level
        # of the street itself (Fairmount Ave). I've seen whole cities go this way, especially when the address isn't technically
        # in that city; e.g. 12345 Sesame Street, SomeTown where the address is really 12345 Sesame Street, OtherTownRightNextDoor.
        # OSM will not find the address and instead drop the best guess at SomeTown. Perhaps there's a Google Maps API call or something
        # we can do here; for now, do it by hand with a lat/lon search.
        chain = ActionChains(driver())
        xpath = "//*[contains(@class, 'geo-dropdown-items')]//button"
        elements = self.elements_by_xpath(xpath)
        if elements == None:
            LOG.warn("No typeahead match at all")
            return False
        typeahead_address_text = elements[0].text
        # TODO: HANDLE MULTIPLE OPTIONS, NOT JUST FIRST TYPEAHEAD
        # Why they didn't implement this as a map escapes me. Translate the zip - ed list of tuples into a map.
        def dictify(zipped_array):
            d = {}
            for (value, key) in usaddress.parse(zipped_array):
                d[key] = value
            return d
        search_address = dictify(self._args.address)
        typeahead_address = dictify(typeahead_address_text)
        LOG.debug(f"Search address: {search_address}")
        LOG.debug(f"Typeahead address: {typeahead_address}")
        chain.click(on_element = elements[0])
        chain.perform()
        LOG.trace("Comparing to typeahead suggestion")
        # Here, we simply detect if they both have an AddressNumber, but better comparisons will probably be more performant.
        if not "AddressNumber" in typeahead_address:
            LOG.warn("No street number detected; assuming inexact match.")
            return False
        # Next failure mode: it finds something similar like halfway around the world.
        address_distance = enchant.utils.levenshtein(self._args.address, typeahead_address_text)
        LOG.debug(f"Levenshtein distance for address search: {address_distance}")
        if address_distance > 15:
            LOG.warn("Large levenshtein distance; not sure about the match.")
            return False
        else:
            LOG.info("Pin dropped at address!")
            return SmappenMyMapPanel.set_map_name(self._args.address)
        
