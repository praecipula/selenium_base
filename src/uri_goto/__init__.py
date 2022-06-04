from base import driver
import logging

"""
This shows what a basic command-based DSL will enable us to do
Simple command: go to a URL
"""

# Define our parser

class Goto:
    name = "goto"

    @classmethod
    def add_command(parent):
        subparser = parent.add_parser("goto")
        subparser.add_argument("uri", metavar='U', type=str, nargs='+', help = "A URL to go to")

def execute(args):
    logger.info("Opening url" + str(args))
    driver.get(args['uri'])
    return True

