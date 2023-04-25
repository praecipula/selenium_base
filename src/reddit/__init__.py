from base import driver, By, Keys, ActionChains, AutomationCommandBase, CommandParser, ASSERT
from base.repl import drop_into_repl
import logging
import os
import yaml

LOG = logging.getLogger(__name__)

class RedditBase(AutomationCommandBase):
    pass


class RedditEnsureLogin(RedditBase):
    name = "reddit_ensure_login"
    base_url = "https://www.reddit.com/"
    login_url = "https://www.reddit.com/login"
    credentials_file = f"{os.path.dirname(__file__)}/credentials.yaml"

    parser = CommandParser(prog = name, description=f'{name} command')

    def do_login(self):
        # Go to login page
        LOG.info("Logging in... ")
        driver.get(RedditEnsureLogin.login_url)

        #Get creds
        credentials = {}
        with open(RedditEnsureLogin.credentials_file, 'r') as creds_file:
            try:
                credentials = yaml.safe_load(creds_file)
            except yaml.YAMLError as e:
                LOG.error("Caught exception in loading yaml file")
                raise

        chain = ActionChains(driver)
        
        LOG.trace("Entering in email address")
        username_xpath = "//input[@id='loginUsername']"
        element = self.element_by_xpath(username_xpath)
        chain.click(on_element=element)
        chain.send_keys_to_element(element, credentials['user'])
        chain.perform()

        LOG.trace("Entering in password")
        username_xpath = "//input[@id='loginPassword']"
        element = self.element_by_xpath(username_xpath)
        chain.click(on_element=element)
        chain.send_keys_to_element(element, credentials['pass'])
        chain.send_keys_to_element(element, Keys.ENTER)
        chain.perform()

        #Stupid popup
        close_interests_xpath = "//button[@aria-label='Close']"
        element = self.element_by_xpath(close_interests_xpath).click()

        return True

    def execute(self):
        LOG.info("Checking for login... ")
        # Go to the root page
        # Check to see if the page lists our profile
        if driver.current_url != RedditEnsureLogin.base_url:
            driver.get(RedditEnsureLogin.base_url)

        #First, see if we can find the button that links to the login page
        login_element_xpath = "//a[starts-with(@href, 'https://www.reddit.com/login/')]"
        elements = self.elements_by_xpath(login_element_xpath)
        if len(elements) != 0:
            # We actually expect this. It'd be unusual to be logged in.
            if not self.do_login():
                LOG.error("Unable to log in for some reason.")
                return False
        return True

    def __str__(self):
        return f"{self.__class__.name}: {self._args}"

