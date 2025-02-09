#!/usr/bin/env python
import base
import logging
import sys

import uri_open
import uri_goto
import base.set_tab_title
import screenshot
import smappen
import smappen.binary_search_for_latlon
import smappen.create_isodistance
import smappen.download
import google_maps
import reddit
import reddit.load_infinite_posts_pages
import reddit.open_subreddit_top_all_time
import reddit.image_post_data_storage
import reddit.capture_all_image_urls
import reddit.create_canonical_imgur_links
import mouse_and_key.wanikani_to_anki
import crunchbase.crunchbase_search_data
import crunchbase.crunchbase_company_profile
import crunchbase.crunchbase_parse_search

CLOSE_ON_EXIT = False
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.TRACE)


class CommandCollection:
    """
    Kind of feels like recreating argparse in a way, but argparse doesn't lend itself to more than one co-existing command.
    This will split commands and work with our DSL even with multiple commands
    """
    def __init__(self):
        self._command_factories = []

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

        self._commands = []
        current_factory = None
        arguments_buffer = []

        def flush():
            nonlocal current_factory, arguments_buffer
            if current_factory:
                LOG.trace("Aggregating args for last command %s: %s", current_factory.name, arguments_buffer)
                # "Flush" current command, which is just-now-determined-to-be "last" command
                # as we've found a new command name. That is, send the aggregated arguments
                # to a new instance of the just-now-"last" command before clearing for the
                # just-now "current" command
                command_instance = current_factory(arguments_buffer)
                LOG.debug("Command: %s", command_instance)
                self._commands.append(command_instance)
                # Set up the next command factory by clearing buffers
                current_factory = None
                arguments_buffer = []

        for token in argument_str:
            token_is_command = False
            for c in self._command_factories:
                if c.name == token:
                    token_is_command = True
                    LOG.trace("Found new command %s", c.name)
                    flush()
                    current_factory = c
                    next
            # We didn't register as a command name, it must be an argument.
            if not token_is_command:
                LOG.trace("Not a command, assuming an argument %s", token)
                arguments_buffer.append(token)
        # If there is a current factory (typical for the last factory we were building) there won't be a "next"
        # command name to trigger aggregation and building, so just flush manually at the end.
        flush()

    @property
    def commands(self):
        return self._commands

    def execute(self):
        if len(self._commands) == 0:
            LOG.debug("No commands built; print help statement")
            #TODO: make this print each commands' help statement instead
            print("Available commands:")
            for command in self._command_factories:
                print(command.name)
        for c in self._commands:
            success = c.execute()
            if not success:
                LOG.critical(f"Command {c} returned false from execution; stopping")
                return False
        LOG.info("Complete!")
        return True



print(sys.argv)

def get_command_collection():
    cc = CommandCollection()
    cc.register_command(uri_open.Open)
    cc.register_command(uri_goto.Goto)
    cc.register_command(screenshot.Screenshot)
    cc.register_command(smappen.SmappenEnsureLogin)
    cc.register_command(smappen.SmappenSearchForLocation)
    cc.register_command(smappen.binary_search_for_latlon.SmappenSearchForLatLon)
    cc.register_command(smappen.binary_search_for_latlon.SmappenSearchForLatLon)
    cc.register_command(smappen.binary_search_for_latlon.SmappenSearchForGoogleMapsPin)
    cc.register_command(smappen.create_isodistance.SmappenCreateIsodistance)
    cc.register_command(smappen.download.SmappenDownload)
    cc.register_command(base.set_tab_title.SetTabTitle)
    cc.register_command(google_maps.GoogleMapsSearchFor)
    cc.register_command(reddit.RedditEnsureLogin)
    cc.register_command(reddit.load_infinite_posts_pages.RedditLoadInfinitePostsPages)
    cc.register_command(reddit.open_subreddit_top_all_time.RedditOpenSubredditTopAllTime)
    cc.register_command(reddit.capture_all_image_urls.RedditCaptureAllImageUrls)
    cc.register_command(reddit.image_post_data_storage.Storage)
    cc.register_command(reddit.create_canonical_imgur_links.RedditNormalizeImageLocations)
    cc.register_command(mouse_and_key.wanikani_to_anki.WanikaniGetVocab)
    cc.register_command(crunchbase.crunchbase_search_data.CrunchbaseSearch)
    cc.register_command(crunchbase.crunchbase_company_profile.CrunchbaseCompanyProfile)
    cc.register_command(crunchbase.crunchbase_parse_search.CrunchbaseParseSearch)
    return cc

if __name__ == "__main__":
    cc = get_command_collection()
    cc.build_commands(sys.argv[1:])
    cc.execute()

if CLOSE_ON_EXIT:
    base.driver().close()
