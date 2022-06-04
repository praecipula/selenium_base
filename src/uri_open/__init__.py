from base import driver
import logging
import argparse

"""
This shows what a basic command-based DSL will enable us to do
Simplest command: open a URL
"""

# Define our parser


class Open:
    name = "open"

    parser = argparse.ArgumentParser(description='Multiple subparsers')
    parser.add_argument("uri", metavar='U', type=str, nargs='+', help = "A URL to go to")

    def __init__(self, command_string):
        self._command_string = command_string
        args = Open.parser.parse_args(command_string)
        print(args)
        

    def execute(args):
        logger.info("Opening url in a new tab" + str(args))
        driver.get(args['uri'])
        return True


