#!/usr/bin/env python
import base
import logging
import sys

import uri_open
import uri_goto
import smappen

CLOSE_ON_EXIT = True
LOG = logging.getLogger(__name__)


class CommandCollection:
    """
    Kind of feels like recreating argparse in a way, but argparse doesn't lend itself to more than one co-existing command.
    This will split commands and work with our DSL even with multiple commands
    """
    def __init__(self):
        self._command_factories = []
        self._commands = []

    def register_command(self, command_factory):
        """
        Add a command factory - typically the class that provides the functionality of the command, but can be any object
        that responds to a "build_command" function with a string.
        """
        self._command_factories.append(command_factory)


    def build_commands(self, argument_str):
        """
        Simple implementation at first
        Loop over every command, and if its name matches the command, start adding the following non-matching arguments to that command.

        TODO: delegate to factories to decide if they can handle a set of arguments (can we use argparse for this proactively somehow?)
        """
        current_factory = None
        commands_buffer = []
        for token in argument_str:
            for c in self._command_factories:
                if c.name == token:
                    LOG.debug("Found new command " + token)
                    print("Found new command " + token)
                    # "Flush" current command, that is, build it with the tokens so far.
                    # Set up the next command factory
                    current_factory = c
                    commands_buffer = []
                    next


print(sys.argv)
cc = CommandCollection()
cc.register_command(uri_open.Open)
cc.register_command(uri_goto.Goto)

cc.build_commands(sys.argv[1:])

if CLOSE_ON_EXIT:
    base.driver.close()
