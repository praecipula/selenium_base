from base import driver, By, Keys, ActionChains, AutomationCommandBase, CommandParser, ASSERT
from base.repl import drop_into_repl
import logging
import argparse
import os
import enchant
import time

LOG = logging.getLogger(__name__)

class GoogleMapsSearchFor(AutomationCommandBase):
    name = "google_maps_search_for"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("address", metavar='ADDRESS', type=str)

    def execute(self):
        LOG.info(f"Searching for address in Google Maps: {self._args.address}")
        chain = ActionChains(driver())
        xpath = "//*[@id='searchboxinput']"
        element=self.element_by_xpath(xpath)
        chain.click(on_element = element)
        chain.send_keys_to_element(element, self._args.address)
        chain.send_keys_to_element(element, Keys.ENTER)
        chain.perform()
        time.sleep(5)
        # Get the URI of the page
        #TODO: Generalize this so all commands are using a results map
        self._results["url"] = driver().current_url
        LOG.info(self._results["url"])
        return True

#class SmappenSearchForLocation(AutomationCommandBase):
#    
#    def execute(self):
#        panel = SmappenParamsPanel()
#        if panel.is_open():
#            LOG.debug("Panel is open")
#            panel.close()
#        else:
#            LOG.debug("Panel is closed")
#            # Do nothing
#        # Normalize the address by parsing and reemitting it in a standard format
#        # TODO: this code will only work for this use case. It's going to likely need something
#        # significantly more robust.
#        # Find the search address bar and enter in the address
#        LOG.trace("Entering in address")
#        xpath = "//*[@id='search-address-bar']//input[@type='text']"
#        element = self.element_by_xpath(xpath)
#        chain.click(on_element=element)
#        chain.send_keys_to_element(element, self._args.address)
#        chain.perform()
#        # Choose the first result. TODO: evaluate match quality vs. input; sometimes the OpenStreetMap results don't find the thing.
#        # Example is the address "623 Fairmount Ave"; it can't find the street number, so zooms out to the next closest match level
#        # of the street itself (Fairmount Ave). I've seen whole cities go this way, especially when the address isn't technically
#        # in that city; e.g. 12345 Sesame Street, SomeTown where the address is really 12345 Sesame Street, OtherTownRightNextDoor.
#        # OSM will not find the address and instead drop the best guess at SomeTown. Perhaps there's a Google Maps API call or something
#        # we can do here; for now, do it by hand with a lat/lon search.
#        chain = ActionChains(driver())
#        xpath = "//*[contains(@class, 'geo-dropdown-items')]//button"
#        elements = self.elements_by_xpath(xpath)
#        typeahead_address_text = elements[0].text
#        # TODO: HANDLE MULTIPLE OPTIONS, NOT JUST FIRST TYPEAHEAD
#        # Why they didn't implement this as a map escapes me. Translate the zip - ed list of tuples into a map.
#        def dictify(zipped_array):
#            d = {}
#            for (value, key) in usaddress.parse(zipped_array):
#                d[key] = value
#            return d
#        search_address = dictify(self._args.address)
#        typeahead_address = dictify(typeahead_address_text)
#        LOG.debug(f"Search address: {search_address}")
#        LOG.debug(f"Typeahead address: {typeahead_address}")
#        chain.click(on_element = elements[0])
#        chain.perform()
#        LOG.trace("Comparing to typeahead suggestion")
#        # Here, we simply detect if they both have an AddressNumber, but better comparisons will probably be more performant.
#        if not "AddressNumber" in typeahead_address:
#            LOG.warn("No street number detected; assuming inexact match.")
#            return False
#        # Next failure mode: it finds something similar like halfway around the world.
#        address_distance = enchant.utils.levenshtein(self._args.address, typeahead_address_text)
#        LOG.debug(f"Levenshtein distance for address search: {address_distance}")
#        if address_distance > 15:
#            LOG.warn("Large levenshtein distance; not sure about the match.")
#            return False
#        else:
#            LOG.info("Pin dropped at address!")
#            return SmappenMyMapPanel.set_map_name(self._args.address)
#        
