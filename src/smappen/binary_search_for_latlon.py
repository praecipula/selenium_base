#!/usr/bin/env python3

# OK, I kind of hate this.

# Smappen won't take in a lat, lon address in its address search, and as a next-gen app it doesn't have any URL params that we can spoof.
# If you right click on the map you can set a lat, lon address as the starting point, but that seems to totally bypass the address bar -
# if you do this, you can see the address in the area definition bar, but it's not registered as valid and you can't submit UNLESS
# you've selected in the map.
# So Google search for lat, lon (to be done by the API later) and run this to find the placemarker for Google's address in Smappen.

from base import driver, By, ASSERT, AutomationCommandBase, CommandParser

import time
import math
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from smappen import SmappenParamsPanel, SmappenMyMapPanel

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

class MouseCoords():
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        self._x = x

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, x):
        self._y = x

    def __sub__(self, other):
        return MouseCoords(self.x - other.x, self.y - other.y)

    def distance(self, other = None):
        """
        Get the magnitude of displacement to other.
        When called with a None other, consider this MouseCoords to be a delta coordinate (from, say __sub__)
        and get its own distance / distance from 0, 0
        """
        if other == None:
            other = MouseCoords(0, 0)
        return math.sqrt((self.x-other.x)**2 + (self.y-other.y)**2)


    def __str__(self):
        return f"🐁 {self.x} {self.y}"

class SmappenSearchForLatLon(AutomationCommandBase):

    name = "smappen_search_for_lat_lon"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("latitude", metavar='LATITIUDE', type=float)
    parser.add_argument("longitude", metavar='LONGITUDE', type=float)
    parser.add_argument("map_name", metavar='MAPNAME', type=str, nargs='?')

    def set_map_pin(self, coords = MouseCoords(0, 0)):
        map_element = self.element_by_xpath("//*[contains(@class, 'map-main')]//*[contains(@class, 'fixed-widget')]")
        a = ActionChains(driver())
        LOG.trace("Moving mouse to offset %s", coords)
        a.move_to_element(map_element)
        # Find the offset - I think this is peculiar to Smappen, it doesn't perfectly recenter the map.
        # 125 - half the width of the analysis panel. #analysis-panel
        smappen_map_recentering = driver().find_element(By.ID, "analysis-panel").size['width'] / 2
        a.move_by_offset(coords.x-smappen_map_recentering, coords.y)
        a.context_click()
        a.move_by_offset(10, 10)
        a.click()
        a.perform()

    def zoom_in(self):
        map_element = self.element_by_xpath("//*[contains(@class, 'map-main')]//*[contains(@class, 'fixed-widget')]")
        a = ActionChains(driver())
        #a.send_keys_to_element(map_element, Keys.ARROW_UP)
        a.send_keys_to_element(map_element, "+")
        a.perform()

    def zoom_way_out(self):
        map_element = self.element_by_xpath("//*[contains(@class, 'map-main')]//*[contains(@class, 'fixed-widget')]")
        a = ActionChains(driver())
        #a.send_keys_to_element(map_element, Keys.ARROW_UP)
        for _ in range(1,10):
            a.send_keys_to_element(map_element, "-")
        a.perform()
    
    def get_map_pin_loc(self):
        # Get the lat, lon from the input bar
        xpath = "//*[@id='search-address-bar']//input[@type='text']"
        element = self.element_by_xpath(xpath)
        pin_latlon = element.get_attribute("value").split(", ")
        LOG.info(pin_latlon)
        return LatLon(pin_latlon[0], pin_latlon[1])

    def execute(self):
        search_latlon = LatLon(self._args.latitude, self._args.longitude)

        panel = SmappenParamsPanel()
        if panel.is_open():
            panel.close()
        time.sleep(0.5)

        if self._args.map_name:
            LOG.debug(f"Setting map name to {self._args.map_name}")
            SmappenMyMapPanel.set_map_name(self._args.map_name)

        mouse_bounds = 150 #how far the mouse can move
        bounds = 0.1 #latlon box to search in (how tight to match), great circle km. (0.1km is 328 feet - too tight?)
        lat_scale = 1000 #Arbitrary scaling factor; initial mouse pixels per degree
        lon_scale = 1000 #Arbitrary scaling factor; initial mouse pixels per degree
        freeze_zoom = False # don't zoom every time, instead give a "skip" round to measure the new zoom pixels/degree.
        # I don't like this flow control, but because longitude changes depending on where you are (the orange slices of "longitude" get fatter in the middle at the equator than they are near the poles) it feels best to do this experiementally, i.e. try it and see.
        # It might be more effective to codify this as an experiment, i.e. "do some stuff to measure distance and return to start", but I'm not fussed that much about it yet. Solve it with comments.
        zoom_depth = 15 # Total zoom iterations before stopping zoom in. Another flow control var that seems wrong, but it's hard to detect "we've zoomed in all the way" without digging into JS in the browser which I'm philisophically opposed to (anything that uses the browser but is fragile to external change, but can be done in the "dumb" way, should be done in the "dumb" way).
        self.zoom_way_out()
        self.set_map_pin()
        pin_latlon = self.get_map_pin_loc()
        search_delta = search_latlon - pin_latlon
        LOG.trace(f"Found search delta of %s", search_delta)
        loop_count = 0
        max_loop_count = 100
        while (search_latlon.gc_distance(pin_latlon) > bounds and loop_count < max_loop_count):
            LOG.debug("Iteration %s", loop_count)
            mouse_delta = MouseCoords(0, 0)
            if search_delta.lon > 0:
                LOG.trace("Move east")
                # Lon (x) Delta is positive (east to the search point) and large
                # This means we need to move east up to the bounds
                mouse_delta.x = min(mouse_bounds, lon_scale*search_delta.lon)
            if search_delta.lon < 0:
                LOG.trace("Move west")
                # Lon (x) Delta is negative (west to the search point) and large
                # This means we need to move west up to the bounds
                mouse_delta.x = max(-mouse_bounds, lon_scale*search_delta.lon)

            if search_delta.lat > 0:
                LOG.trace("Move north")
                # lat (y) Delta is positive (north to the search point) and large
                # This means we need to move north up to the bounds WHICH IS -Y ON THE MOUSE COORDS
                mouse_delta.y = -min(mouse_bounds, lat_scale*search_delta.lat)
            if search_delta.lat < 0:
                LOG.trace("Move south")
                # lat (y) Delta is negative (south to the search point) and large
                # This means we need to move south up to the bounds WHICH IS +Y ON THE MOUSE COORDS
                mouse_delta.y = -max(-mouse_bounds, lat_scale*search_delta.lat)

            LOG.debug("Mouse delta: %s", mouse_delta)
            if mouse_delta.distance() < 100 and not freeze_zoom and zoom_depth > 0:
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
            self.set_map_pin(mouse_delta)
            pin_latlon = self.get_map_pin_loc()
            LOG.trace("Pin location %s", pin_latlon)
            pin_delta = pin_latlon - last_pin_latlon
            LOG.trace("Pin delta %s", pin_delta)

            search_delta = search_latlon - pin_latlon
            
            # Recalculate scaling factor for next loop
            # Don't forget, as strange as this is, mouse[1](y) is latitude (latlon[0])
            # Also, note we cap the div/0 with some set very small amount
            lat_scale = min(max(abs(mouse_delta.y / (pin_delta.lat or 0.01)), 10), 100000)
            lon_scale = min(max(abs(mouse_delta.x / (pin_delta.lon or 0.01)), 10), 100000)
            LOG.trace(f"Found search delta of %s, (%s km), scale %s , %s", search_delta, search_latlon.gc_distance(pin_latlon), lat_scale, lon_scale)

            loop_count = loop_count + 1

        LOG.trace("Done looping")
        if loop_count >= max_loop_count:
            return False
        return True


class SmappenSearchForGoogleMapsPin(SmappenSearchForLatLon):

    name = "smappen_search_for_google_maps_pin"

    parser = CommandParser(prog = name, description=f'{name} command')
    parser.add_argument("maps_uri", type=str)
    parser.add_argument("map_name", metavar='MAPNAME', type=str, nargs='?')

    def __init__(self, command_args):
        super().__init__(command_args)
        search_latlon_values = self._args.maps_uri[self._args.maps_uri.find("@")+1:self._args.maps_uri.find("z/")-3].split(",")
        self._args.latitude = search_latlon_values[0]
        self._args.longitude = search_latlon_values[1]
        
