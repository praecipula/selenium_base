from base import driver, ActionChains, AutomationCommandBase, CommandParser
import logging
import argparse
import os
import usaddress

LOG = logging.getLogger(__name__)

class SmappenParamsPanel:
    element_css = ".create-area-panel"

    def __init__(self):
        elements = driver.find_elements_by_css_selector(self.__class__.element_css)
        if len(elements) != 1:
            LOG.critical("Got more or less than 1 panel")
            exit(-1)
        self._panel = elements[0]

    def is_open(self):
        if self._panel.get_attribute("class").find("open") > -1:
            return True
        return False

    def create_area(self):
        chain = ActionChains(driver)
        LOG.trace("Creating new area")
        add_panel_button_xpath = "//*[@data-cy='add-area']"
        button = AutomationCommandBase.element_by_xpath(add_panel_button_xpath)
        chain.click(on_element=button)
        chain.perform()
        return True


    def close(self):
        chain = ActionChains(driver)
        LOG.trace("Closing area creation panel")
        close_panel_button_xpath = "//*[@data-cy='close-create-area-panel']"
        button = AutomationCommandBase.element_by_xpath(close_panel_button_xpath)
        chain.click(on_element=button)
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
        if driver.current_url != SmappenEnsureLogin.base_url:
            driver.get(SmappenEnsureLogin.base_url)


        login_button_xpath = "//*[@data-cy='desktop-navbar-login-button']"
        element = self.element_by_xpath(login_button_xpath)
        if not element:
            LOG.info("Could not find element, we think we're logged in already.")
            LOG.trace("TODO: implement a real non-null check to verify we are logged in.")
            return True
        LOG.info(f"Successfully detected we are not logged in")
        driver.get(SmappenEnsureLogin.login_url)
        # Prefer action chains - they will generally be human-ish enough to get the job done even
        # for times we need onBlur or onMouseMove
        chain = ActionChains(driver)
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
        chain = ActionChains(driver)
        xpath = "//*[@id='search-address-bar']//input[@type='text']"
        element = self.element_by_xpath(xpath)
        chain.click(on_element=element)
        chain.send_keys_to_element(self._args.address)
        chain.perform()
        # Choose the first result. TODO: evaluate match quality vs. input; sometimes the OpenStreetMap results don't find the thing.
        # Example is the address "623 Fairmount Ave"; it can't find the street number, so zooms out to the next closest match level
        # of the street itself (Fairmount Ave). I've seen whole cities go this way, especially when the address isn't technically
        # in that city; e.g. 12345 Sesame Street, SomeTown where the address is really 12345 Sesame Street, OtherTownRightNextDoor.
        # OSM will not find the address and instead drop the best guess at SomeTown. Perhaps there's a Google Maps API call or something
        # we can do here; for now, do it by hand.
        LOG.trace("Comparing to typeahead suggestion")
        xpath = "//*[contains(@class, 'geo-dropdown-items')]//button"
        elements = self.elements_by_xpath(xpath)
        import pdb; pdb.set_trace()
