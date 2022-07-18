#!/usr/bin/env python

import re
from multiprocessing import Pool
import logging
import base
import webby

LOG = logging.getLogger(__name__)

addresses = """
Tahoe City, CA Supercharger
140 Lake Boulevard
Tahoe City, CA 96145
Roadside Assistance : (877) 798-3752
Tejon Ranch Supercharger
5602 Dennis McCarthy Dr
Lebec, CA 93243
Roadside Assistance : (877) 798-3752
Tejon Ranch, CA – Outlets at Tejon Pkwy Supercharger
5701 Outlets at Tejon Parkway
Arvin, CA 93203
Roadside Assistance : (877) 798-3752
Temecula Supercharger
40820 Winchester Rd.
Temecula, CA 92591
Roadside Assistance : (877) 798-3752
Temecula, CA (coming soon)
Temecula, CA
Temecula, CA - Temecula Parkway Supercharger
30515 Temecula Parkway
Temecula, CA 92592
Roadside Assistance : (877) 798-3752
Thousand Oaks, CA - East Thousand Oaks Boulevard Supercharger
4000 East Thousand Oaks Boulevard
Thousand Oaks, 91362
Roadside Assistance : (877) 798-3752
Thousand Oaks, CA - West Hillcrest Drive Supercharger
350 West Hillcrest Drive
Thousand Oaks, CA 91360
Roadside Assistance : (877) 798-3752
Torrance, CA (coming soon)
Torrance, CA
Torrance, CA Supercharger
3490 Fashion Way
Torrance, CA 90503
Roadside Assistance : (877) 798-3752
Tracy, CA - West Grant Line Road Supercharger
2850 West Grant Line Road
Tracy, CA 95304
Roadside Assistance : (877) 798-3752
Traver, CA Supercharger
36005 CA-99
Traver, CA 93673
Roadside Assistance : (877) 798-3752
Truckee Brockway Road Supercharger
11209 Brockway Road
Truckee, CA 96161
Roadside Assistance : (877) 798-3752
Truckee Donner Pass Supercharger
11290 Donner Pass Rd
Truckee, CA 96161
Roadside Assistance : (877) 798-3752
Truckee, CA - Soaring Way Supercharger
Soaring Way
Truckee, CA
Roadside Assistance : (877) 798-3752
Turlock, CA (coming soon)
Turlock, CA
Tustin, CA (coming soon)
Tustin, CA
Tustin, CA Supercharger
15160 Kensington Park Drive
Tustin, CA 92782
Roadside Assistance : (877) 798-3752
Twentynine Palms Supercharger
73829 Baseline Road
Twentynine Palms, CA 92277-4125
Roadside Assistance : (877) 798-3752
"""

# Take out "Roadside Assistance"

search_roadside_assistance_regex = r'.*Roadside Assistance.*'
def remove_roadside_assistance(string_list):
    global search_roadside_assistance_regex
    return list(filter(lambda l: re.search(search_roadside_assistance_regex, l) == None, string_list))

search_coming_soon_regex = r'.*coming soon.*'
def remove_coming_soon(string_list):
    global search_coming_soon_regex
    skip_next = False
    kept_lines = []
    for line in string_list:
        if re.search(search_coming_soon_regex, line) != None:
            skip_next = True
            continue # without collecting the line
        if skip_next == True:
            skip_next = False
            continue #without collecting the line
        # collect the line
        kept_lines.append(line)
    return kept_lines

search_supercharger_regex = r'.*Supercharger.*'
def remove_supercharger_title(string_list):
    global search_supercharger_regex
    return list(filter(lambda l: re.search(search_supercharger_regex, l) == None, string_list))

def join_every_other_line_to_address(string_list):
    aggregate = []
    for lineno, line in enumerate(string_list):
        if lineno % 2 == 1:
            continue
        aggregate.append(AddressLine(line + ", " + string_list[lineno + 1])) # Should not out of index for well-formed (even counted) inputs
    return aggregate


class AddressLine:

    def __init__(self, address):
        self._address = address
        self._success_by_address = None

    @property
    def success_by_address(self):
        return self._success_by_address

    @success_by_address.setter
    def success_by_address(self, success):
        self._success_by_address = success

    @property
    def address(self):
        return self._address

    def __repr__(self):
        return f"Addr: {self.address}, by_address: {self._success_by_address}"

def execute_name_based_search(address_line):
    LOG.info(f"Executing name based search for {address_line.address}")
    cc = webby.get_command_collection()
    cc.build_commands([
        'open', "https://smappen.com/app",
        "smappen_ensure_login",
        "smappen_search_for_location", f"{address_line.address}",
        "smappen_create_isodistance", "1.6",
        "smappen_create_isodistance", "8",
        "smappen_create_isodistance", "16",
        "smappen_create_isodistance", "32",
        "smappen_create_isodistance", "80",
        "smappen_create_isodistance", "160",
        "smappen_create_isodistance", "241",
        "smappen_create_isodistance", "321",
        "smappen_create_isodistance", "402",
        "smappen_create_isodistance", "483",
        "set_tab_title", "(***DONE***)"
    ])
    address_line.success_by_address = cc.execute()
    return address_line

if __name__ == "__main__":

    no_blanks = [l for l in addresses.splitlines() if l != '']
    no_roadside = remove_roadside_assistance(no_blanks)
    no_coming_soon = remove_coming_soon(no_roadside)
    no_supercharger_title = remove_supercharger_title(no_coming_soon)
    address_lines = join_every_other_line_to_address(no_supercharger_title)

    print(address_lines)

    with Pool(processes=2) as pool:
        result = pool.map(execute_name_based_search, address_lines[0:4])
        LOG.info("Result: " + str(result))
    LOG.info("Finished with execution!")

