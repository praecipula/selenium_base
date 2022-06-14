from base import driver, AutomationCommandBase, CommandParser
import logging
import argparse

"""
This shows what a basic command-based DSL will enable us to do
Simplest command: open a URL
"""

LOG = logging.getLogger(__name__)

class Open(AutomationCommandBase):
    name = "open"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("uri", metavar='URI', type=str)

    def execute(self):
        LOG.info("Opening new tab at " + self._args.uri)
        driver.get(self._args.uri)
        return True

