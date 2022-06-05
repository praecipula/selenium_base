from base import driver
import logging
import argparse

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

class Open:
    name = "open"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("uri", metavar='URI', type=str)

    def __init__(self, command_args):
        self._argstr = command_args
        self._args = Open.parser.parse_args(command_args)
        

    def execute(self):
        LOG.info("Opening new tab at " + self._args.uri)
        driver.get(self._args.uri)
        return True

    def __str__(self):
        return f"{self.__class__.name}: {self._args}"


