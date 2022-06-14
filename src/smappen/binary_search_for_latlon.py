#!/usr/bin/env python3

# OK, I kind of hate this.

# Smappen won't take in a lat, lon address in its address search, and as a next-gen app it doesn't have any URL params that we can spoof.
# If you right click on the map you can set a lat, lon address as the starting point, but that seems to totally bypass the address bar -
# if you do this, you can see the address in the area definition bar, but it's not registered as valid and you can't submit UNLESS
# you've selected in the map.
# So Google search for lat, lon (to be done by the API later) and run this to find the placemarker for Google's address in Smappen.

from base import driver, ASSERT

import webby
import time
import math
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from smappen import SmappenParamsPanel

import logging



LOG = logging.getLogger(__name__)


class LatLon:

    def __init__(self, latitude, longitude, altitude = 0):
        self._lat = self._validate_degrees(latitude)
        self._lon = self._validate_degrees(longitude)
        self._alt = float(altitude)
    
    @staticmethod
    def _validate_degrees(deg):
        d = float(deg)
        ASSERT(-180 <= d <= 180, f"Degree value of {deg} must be between -180 and 180 inclusive")
        return float(d)

    @property
    def lat(self):
        return self._lat

    @lat.setter
    def lat(self, latitude):
        self._lat = self._validate_degrees(latitude)

    @property
    def lon(self):
        return self._lon

    @lon.setter
    def lon(self, longitude):
        self._lon = self._validate_degrees(longitude)

    @property
    def alt(self):
        return self._alt

    @alt.setter
    def alt(self, altitude):
        # Unbound. should we do validation / bounding on e.g. negative altitudes?
        self._alt = altitude

    def __sub__(self, other):
        return LatLon(self.lat - other.lat, self.lon - other.lon, self.alt - other.alt)

    def gc_distance(self, other):
        """
        Great circle distance between self and other (scalar, km) - to be used by non-delta vectors
        """
        # Pulled from https://undergroundmathematics.org/trigonometry-compound-angles/the-great-circle-distance
        # sin**2(d/2R) = sin**2(other.lat - self.lat / 2) + cos(self.lat)*cos(other.lat)sin**2(other.lon - this.lon / 2)
        #sin(d/2R) = sqrt(sin**2(other.lat - self.lat / 2) + cos(self.lat)*cos(other.lat)sin**2(other.lon - this.lon / 2))
        # d = 2R*asin(sqrt(sin**2(other.lat - self.lat / 2) + cos(self.lat)*cos(other.lat)sin**2(other.lon - this.lon / 2)))
        DEG2R = 0.0174533
        try:
            return 2*6378*math.asin(
                math.sqrt(
                    math.sin((DEG2R*other.lat - DEG2R*self.lat) / 2)**2 +
                    math.cos(DEG2R*self.lat)*math.cos(DEG2R*other.lat) *
                    math.sin((DEG2R*other.lon - DEG2R*self.lon) / 2)**2
                )
            )
        except ValueError as e:
            ASSERT(e)


    def __str__(self):
        return f"🧭 {self.lat} {self.lon} {self.alt}"
        

class PlacemarkFinder:

    def set_map_pin(self, offsetx = 0, offsety = 0):
        map_element = driver.find_element_by_xpath("//*[contains(@class, 'map-main')]//*[contains(@class, 'fixed-widget')]")
        a = ActionChains(driver)
        LOG.trace("Moving mouse to offset %s, %s", offsetx, offsety)
        a.move_to_element(map_element)
        # Find the offset - I think this is peculiar to Smappen, it doesn't perfectly recenter the map.
        # 125 - half the width of the analysis panel. #analysis-panel
        smappen_map_recentering = driver.find_element_by_id("analysis-panel").size['width'] / 2
        a.move_by_offset(offsetx-smappen_map_recentering, offsety)
        a.context_click()
        a.move_by_offset(10, 10)
        a.click()
        a.perform()

    def zoom_in(self):
        map_element = driver.find_element_by_xpath("//*[contains(@class, 'map-main')]//*[contains(@class, 'fixed-widget')]")
        a = ActionChains(driver)
        #a.send_keys_to_element(map_element, Keys.ARROW_UP)
        a.send_keys_to_element(map_element, "+")
        a.perform()

    def zoom_way_out(self):
        map_element = driver.find_element_by_xpath("//*[contains(@class, 'map-main')]//*[contains(@class, 'fixed-widget')]")
        a = ActionChains(driver)
        #a.send_keys_to_element(map_element, Keys.ARROW_UP)
        for _ in range(1,10):
            a.send_keys_to_element(map_element, "-")
        a.perform()
    
    def get_map_pin_loc(self):
        # Get the lat, lon from the input bar
        xpath = "//*[@id='search-address-bar']//input[@type='text']"
        element = driver.find_element_by_xpath(xpath)
        pin_latlon = element.get_attribute("value").split(", ")
        LOG.info(pin_latlon)
        return LatLon(pin_latlon[0], pin_latlon[1])

    def execute(self):

        webby.cc.build_commands("open https://smappen.com/app".split(" "))
        webby.cc.execute()
        gmaps_address = "https://www.google.com/maps/place/2220+Bridgepointe+Pkwy,+San+Mateo,+CA+94404/@37.5583346,-122.2843335,43m/data=!3m1!1e3!4m5!3m4!1s0x808f9ec39ceebaf5:0x3aed7a290921ae36!8m2!3d37.558541!4d-122.2832881"
        search_latlon_values = gmaps_address[gmaps_address.find("@")+1:gmaps_address.find("z/")-3].split(",")
        search_latlon = LatLon(search_latlon_values[0], search_latlon_values[1])

        panel = SmappenParamsPanel()
        if panel.is_open():
            panel.close()





        mouse_bounds = 150 #how far the mouse can move
        bounds = 0.1 #latlon box to search in (how tight to match), great circle km. (0.1km is 328 feet - too tight?)
        lat_scale = 1000 #Arbitrary scaling factor
        lon_scale = 1000 #Arbitrary scaling factor
        freeze_zoom = False
        zoom_depth = 15 # Total zoom iterations. Another flow control var that seems wrong.
        self.zoom_way_out()
        self.set_map_pin()
        pin_latlon = self.get_map_pin_loc()
        search_delta = search_latlon - pin_latlon
        LOG.trace(f"Found search delta of %s", search_delta)
        loop_count = 0
        while (search_latlon.gc_distance(pin_latlon) > bounds and loop_count < 100):
            LOG.debug("Iteration %s", loop_count)
            mouse_delta = [0, 0]
            if search_delta.lon > 0:
                LOG.trace("Move east")
                # Lon (x) Delta is positive (east to the search point) and large
                # This means we need to move east up to the bounds
                mouse_delta[0] = min(mouse_bounds, lon_scale*search_delta.lon)
            if search_delta.lon < 0:
                LOG.trace("Move west")
                # Lon (x) Delta is negative (west to the search point) and large
                # This means we need to move west up to the bounds
                mouse_delta[0] = max(-mouse_bounds, lon_scale*search_delta.lon)

            if search_delta.lat > 0:
                LOG.trace("Move north")
                # lat (y) Delta is positive (north to the search point) and large
                # This means we need to move north up to the bounds WHICH IS -Y ON THE MOUSE COORDS
                mouse_delta[1] = -min(mouse_bounds, lat_scale*search_delta.lat)
            if search_delta.lat < 0:
                LOG.trace("Move south")
                # lat (y) Delta is negative (south to the search point) and large
                # This means we need to move south up to the bounds WHICH IS +Y ON THE MOUSE COORDS
                mouse_delta[1] = -max(-mouse_bounds, lat_scale*search_delta.lat)

            LOG.debug("Mouse delta: %s", mouse_delta)
            if math.sqrt(mouse_delta[0]**2 + mouse_delta[1]**2) < 100 and not freeze_zoom and zoom_depth > 0:
                LOG.trace("Zooming in")
                self.zoom_in()
                # Ensures 2 runs at this level, as the zoom factor is wrong by now. This means we won't zoom but rather recalc.
                freeze_zoom = True
                zoom_depth = zoom_depth - 1
                continue
            # Is there a better way to do self than with loop control with freeze_zoom?
            freeze_zoom = False
            last_pin_latlon = pin_latlon
            LOG.trace("Last pin location %s", last_pin_latlon)
            self.set_map_pin(mouse_delta[0], mouse_delta[1])
            pin_latlon = self.get_map_pin_loc()
            LOG.trace("Pin location %s", pin_latlon)
            pin_delta = pin_latlon - last_pin_latlon
            LOG.trace("Pin delta %s", pin_delta)

            search_delta = search_latlon - pin_latlon
            
            # Recalculate scaling factor for next loop
            # Don't forget, as strange as this is, mouse[1](y) is latitude (latlon[0])
            # Also, note we cap the div/0 with some set very small amount
            lat_scale = min(max(abs(mouse_delta[1] / (pin_delta.lat or 0.01)), 10), 100000)
            lon_scale = min(max(abs(mouse_delta[0] / (pin_delta.lon or 0.01)), 10), 100000)
            LOG.trace(f"Found search delta of %s, (%s km), scale %s , %s", search_delta, search_latlon.gc_distance(pin_latlon), lat_scale, lon_scale)

            loop_count = loop_count + 1

        LOG.trace("Done looping")



if __name__ == "__main__":
    PlacemarkFinder().execute()
