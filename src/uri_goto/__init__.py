from base import driver, AutomationCommandBase, CommandParser
import logging

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.TRACE)

"""
This shows what a basic command-based DSL will enable us to do
Simple command: go to a URL
"""

# Define our parser

class Goto(AutomationCommandBase):
    name = "goto"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("uri", metavar='U', type=str, help = "A URL to go to")

    def execute(self):
        LOG.info("Opening url" + str(self))
        driver().get(self._args.uri)
        return True

