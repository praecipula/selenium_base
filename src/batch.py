#!/usr/bin/env python

import re
from multiprocessing import Pool
import logging
import base
from base import ASSERT
import webby

LOG = logging.getLogger(__name__)
MULTIPROCESSING=True

# Take out "Roadside Assistance"
search_roadside_assistance_regex = r'.*Roadside Assistance.*'
def remove_roadside_assistance(string_list):
    global search_roadside_assistance_regex
    return list(filter(lambda l: re.search(search_roadside_assistance_regex, l) == None, string_list))

# and "Coming Soon"
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

# and the title, which always has "Supercharger"
search_supercharger_regex = r'.*Supercharger.*'
def remove_supercharger_title(string_list):
    global search_supercharger_regex
    return list(filter(lambda l: re.search(search_supercharger_regex, l) == None, string_list))

# Since the addresses are formatted over 2 lines, join them. This *should* work unless there's something wrong with the formatting work up to this point.
def join_every_other_line_to_address(string_list):
    aggregate = []
    ASSERT(len(string_list) % 2 == 0, "We don't have an even number of address strings")
    for lineno, line in enumerate(string_list):
        if lineno % 2 == 1:
            continue
        aggregate.append(AddressLine(line + ", " + string_list[lineno + 1])) # Should not out of index for well-formed (even counted) inputs
    return aggregate


class AddressLine:

    def __init__(self, address, latlon=None):
        self._address = address
        self._success_by_address = None
        self._success_by_latlon = None

    @property
    def success_by_address(self):
        return self._success_by_address

    @success_by_address.setter
    def success_by_address(self, success):
        self._success_by_address = success

    @property
    def success_by_latlon(self):
        return self._success_by_latlon

    @success_by_latlon.setter
    def success_by_latlon(sef, success):
        self._success_by_latlon = success

    @property
    def address(self):
        return self._address

    def latlon(self):
        return self._latlon

    def __repr__(self):
        return f"Addr: {self.address}, by_address: {self._success_by_address}"

#------------------------

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
        "smappen_download",
        "set_tab_title", "(***DONE***)"
    ])
    address_line.success_by_address = cc.execute()
    return address_line

def do_name_based_search():
    # Direct copy paste
    addresses = """
Michigan City, IN Supercharger
5150 Franklin Street
Michigan City, IN 46360
Roadside Assistance : (877) 798-3752
Dows Supercharger
904 Cardinal Lane
Dows, 50071-8004
Roadside Assistance : (877) 798-3752
Kansas
Colby, KS Supercharger
700 E Horton Ave
Colby, KS 67701-3746
Roadside Assistance : (877) 798-3752
El Dorado, KS (coming soon)
El Dorado, KS
Emporia, KS Supercharger
1312 Industrial Road
Emporia, KS 66801
Roadside Assistance : (877) 798-3752
Goodland, KS Supercharger
2631 Enterprise Rd
Goodland, KS 67735
Roadside Assistance : (877) 798-3752
Hays, KS Supercharger
4101 Vine St
Hays, KS 67601
Roadside Assistance : (877) 798-3752
Lawrence, KS Supercharger
209 Kansas Turnpike
Lawrence, KS 66086
Roadside Assistance : (877) 798-3752
Mission, KS Supercharger
6655 Martway Street
Mission, KS 66202
Roadside Assistance : (877) 798-3752
Olathe, KS Supercharger
18101 West 119th Street
Olathe, KS 66061
Roadside Assistance : (877) 798-3752
Overland Park, KS (coming soon)
Overland Park, KS
Russell, KS (coming soon)
Russell, KS
Salina, KS Supercharger
755 W. Diamond Dr.
Salina, KS 67401
Roadside Assistance : (877) 798-3752
Topeka, KS (coming soon)
Topeka, KS
Topeka, KS Supercharger
5930 SW Huntoon St
Topeka, KS 66614
Roadside Assistance : (877) 798-3752
Wichita Kansas Supercharger
4760 S. Broadway Street
Wichita, KS 67216
Roadside Assistance : (877) 798-3752
Kentucky
Beaver Dam, KY Supercharger
675 Western Kentucky Parkway
Beaver Dam, KY 42320
Roadside Assistance : (877) 798-3752
Bowling Green Supercharger
1676 Westpark Drive
Bowling Green, KY 42104
Roadside Assistance : (877) 798-3752
Florence, KY - Houston Road Supercharger
4990 Houston Road
Florence, KY 41042
Roadside Assistance : (877) 798-3752
Kuttawa Supercharger
62 Days Inn Dr
Kuttawa, KY 42055-5954
Roadside Assistance : (877) 798-3752
Lexington Supercharger
2155 Paul Jones Way
Lexington, KY 40509
Roadside Assistance : (877) 798-3752
Lexington, KY (coming soon)
Lexington, KY
London Supercharger
140 Faith Assembly Church Road
London, KY 40741
Roadside Assistance : (877) 798-3752
Louisville Supercharger
2120 Gardiner Ln
Louisville, KY 40205
Roadside Assistance : (877) 798-3752
Louisville, KY - Preston Highway Supercharger
9500 Preston Highway
Louisville, KY 40229
Roadside Assistance : (877) 798-3752
Louisville, KY - Towne Center Drive Supercharger
4100 Towne Center Drive
Louisville, KY 40241
Roadside Assistance : (877) 798-3752
Los Angeles
Los Angeles, CA - Alameda Street Supercharger
787 S. Alameda Street
Los Angeles, CA 90021
Roadside Assistance : (877) 798-3752
Louisiana
Alexandria Supercharger
701 4th Street
Alexandria, LA 71301
Roadside Assistance : (877) 798-3752
Baton Rouge Supercharger
3535 Perkins Road
Baton Rouge, LA 70808
Roadside Assistance : (877) 798-3752
Baton Rouge, LA (coming soon)
Baton Rouge, LA
Covington, LA (coming soon)
Covington, LA
Iowa, LA (coming soon)
Iowa, LA
Iowa, LA Supercharger
800 V F Factory Outlet Drive
Iowa, LA 70647
Roadside Assistance : (877) 798-3752
Lake Charles Supercharger
1772 W Prien Lake Road
Lake Charles, LA 70601
Roadside Assistance : (877) 798-3752
Monroe Supercharger
4919 Pecanland Mall Drive
Monroe, LA 71203
Roadside Assistance : (877) 798-3752
New Orleans, LA (coming soon)
New Orleans, LA
Ruston, LA Supercharger
1407 Eagle Dr
Ruston, LA 71270
Roadside Assistance : (877) 798-3752
Sulphur, LA (coming soon)
Sulphur, LA
Maine
Augusta, ME Supercharger
197 Civic Center Drive
Augusta, ME 4330
Roadside Assistance : (877) 798-3752
Baileyville, ME Supercharger
32 Houlton Rd
Baileyville, ME 4694
Roadside Assistance : (877) 798-3752
Bar Harbor, ME Supercharger
225 High Street
Bar Harbor, ME 04605
Roadside Assistance : (877) 798-3752
Bethel, ME Supercharger
Bethel, ME 04217
Roadside Assistance : (877) 798-3752
Falmouth, ME (coming soon)
Falmouth, ME
Kennebunk, ME North Supercharger
25.5 Mile Maine Turnpike
Kennebunk, ME 4043
Roadside Assistance : (877) 798-3752
Kennebunk, ME South Supercharger
25.5 Mile Maine Turnpike
Kennebunk, ME 4043
Roadside Assistance : (877) 798-3752
Newport, ME (coming soon)
Newport, ME
Saco, ME (coming soon)
Saco, ME
Waterville, ME (coming soon)
Waterville, ME
Wells, ME (coming soon)
Wells, ME
"""


    no_blanks = [l.strip() for l in addresses.splitlines() if l.strip() != '']
    no_roadside = remove_roadside_assistance(no_blanks)
    no_coming_soon = remove_coming_soon(no_roadside)
    no_supercharger_title = remove_supercharger_title(no_coming_soon)
    print(no_supercharger_title)
    address_lines = join_every_other_line_to_address(no_supercharger_title)

    print(address_lines)

    all_results = []
    success_results = []
    fail_results = []
    if MULTIPROCESSING:
        with Pool(processes=3) as pool:
            all_results = pool.map(execute_name_based_search, address_lines[::])
    else:
        all_results = map(execute_name_based_search, address_lines[::])

    for result in all_results:
        if result.success_by_address:
            success_results.append(result)
        else:
            fail_results.append(result)
    LOG.info("Finished with execution!")
    LOG.debug("Successful results: " + str(len(success_results)))
    LOG.info("Unsuccessful results being line-printed presently")
    for result in fail_results:
        print(result.address)

#---------------------------

def execute_latlon_url_lookup(redo_address):
    LOG.info(f"Executing latlon lookup for {redo_address}")
    cc = webby.get_command_collection()
    cc.build_commands([
        'open', "http://maps.google.com",
        'google_maps_search_for', redo_address["address"]
    ])
    success = cc.execute()
    # Look into the results
    print("RESULTS ARE" + cc.commands[1].results['url'])
    redo_address["url"] = cc.commands[1].results['url']
    return redo_address

def do_latlon_url_lookup():
    redos = """
    """

    all_results = []
    success_results = []
    fail_results = []
    payloads = []
    for redo in redos.strip().split("\n"):
        payloads.append({"address": redo})
    with Pool(processes=3) as pool:
        all_results = pool.map(execute_latlon_url_lookup, payloads)
    LOG.info("Printing out lines to copy paste for the next step:")
    for result in all_results:
        print('gl("' + result["address"] + '", "' + result["url"] + '"),')
        

#-----------------------------

class AddressGmapLine:

    def __init__(self, address, gmap):
        self.address = address
        self.gmap = gmap
        self.success = None

    def __repr__(self):
        return f"GmapAddr: {self.address}, gmaps {self.gmap[35:55]}, success: {self.success}"

def execute_latlon_based_search(line):
    LOG.info(f"Executing latlon based search for {line}")
    cc = webby.get_command_collection()
    cc.build_commands([
        'open', "https://smappen.com/app",
        "smappen_ensure_login",
        "smappen_search_for_google_maps_pin", f"\"{line.gmap}\"", f"{line.address}",
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
        "smappen_download",
        "set_tab_title", "(***DONE***)"
    ])
    line.success = cc.execute()
    return line


def do_latlon_based_search():

    def gl(address, google_maps_link):
        return AddressGmapLine(address, google_maps_link)

    redos = [
]

    all_results = []
    success_results = []
    fail_results = []
    with Pool(processes=3) as pool:
        all_results = pool.map(execute_latlon_based_search, redos[::])

    for result in all_results:
        if result.success:
            success_results.append(result)
        else:
            fail_results.append(result)
    LOG.info("Finished with execution!")
    LOG.debug("Successful results: " + str(len(success_results)))
    LOG.info("Unsuccessful results being line-printed presently")
    for result in fail_results:
        print(result.address)


#-----------------------------


if __name__ == "__main__":
    do_name_based_search()
    #do_latlon_url_lookup()
    #do_latlon_based_search()
