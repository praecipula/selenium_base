from base import driver, ActionChains
import logging
import argparse
import os

"""
This shows what a basic command-based DSL will enable us to do
Simplest command: open a URL
"""

LOG = logging.getLogger(__name__)

class CommandParser(argparse.ArgumentParser):

    class ParseError(Exception):
        pass

    def error(self, message):
        LOG.critical(message)
        raise CommandParser.ParseError(message)


class SmappenEnsureLogin:
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

    def __init__(self, command_args):
        self._argstr = command_args
        self._args = type(self).parser.parse_args(command_args)
        

    def execute(self):
        LOG.info("Checking for login... ")
        # Go to the root page
        # Check to see if the page lists our profile
        if driver.current_url != SmappenEnsureLogin.base_url:
            driver.get(SmappenEnsureLogin.base_url)

        def get_element(xpath):
            elements = driver.find_elements_by_xpath(xpath)
            if len(elements) == 0:
                LOG.info("We didn't find any element and think we're logged in.")
                LOG.trace("TODO: implement a real non-null check to verify we are logged in.")
                return None
            if len(elements) != 1:
                LOG.error(f"Could not find the element with xpath {login_button_xpath}")
                return None
            return elements[0]

        login_button_xpath = "//*[@data-cy='desktop-navbar-login-button']"
        element = get_element(login_button_xpath)
        if not element:
            return False
        if element: # We found the "login" button/CTA, meaning we are not in fact logged in.
            LOG.info(f"Successfully detected we are not logged in")
            driver.get(SmappenEnsureLogin.login_url)
            # Prefer action chains - they will generally be human-ish enough to get the job done even
            # for times we need onBlur or onMouseMove
            chain = ActionChains(driver)
            username_xpath = "//input[@type='email']"
            element = get_element(username_xpath)
            chain.click(on_element=element)
            chain.send_keys_to_element(element, "dropclic@gmail.com")
            chain.perform()
            password_xpath = "//input[@type='password']"
            element = get_element(password_xpath)
            chain.click(on_element=element)
            chain.send_keys_to_element(element, os.environ.get('SMAPPEN_PASSWORD'))
            chain.perform()
            login_button_xpath = "//button[@type='submit']"
            element = get_element(login_button_xpath)
            chain.click(on_element=element)
            chain.perform()
            return True




        return True

    def __str__(self):
        return f"{self.__class__.name}: {self._args}"


