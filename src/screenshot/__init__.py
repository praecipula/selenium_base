from base import driver, By, AutomationCommandBase, CommandParser
import logging

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.TRACE)

"""
This shows what a basic command-based DSL will enable us to do
Simple command: go to a URL
"""

# Define our parser

class Screenshot(AutomationCommandBase):
    name = "screenshot"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("image_destination", metavar='d', type=str, nargs='?', help = "A screenshot to capture", default="/tmp/screencapture.png")
    parser.add_argument("full_page", metavar='f', type=bool)

    def execute(self):
        LOG.info("Taking a screenshot" + str(self))
        if self._args.full_page:
            el = driver().find_element(By.TAG_NAME, 'body')
            el.screenshot(self._args.image_destination)
        else:
            driver().save_screenshot(self._args.image_destination)
        return True

