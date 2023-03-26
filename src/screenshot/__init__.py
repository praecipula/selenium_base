from base import driver, AutomationCommandBase, CommandParser
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

    def execute(self):
        LOG.info("Taking a screenshot" + str(self))
        driver.save_screenshot(self._args.image_destination)
        return True

