# This is imported into the module-level namespace, so we can put a bunch of util
# functions in this module for all other modules/classes

import os
import time
import random
import logging
import subprocess
import python_logging_base
from python_logging_base import ASSERT
import pyautogui

LOG = logging.getLogger("clicky.util")
LOG.setLevel(logging.TRACE)

def write_text(text):
    # For some reason it doesn't appear that pyautogui is handling shift well.
    # It doesn't always do this, but sometimes it doesn't shift, other times
    # the shift doesn't cancel. I can't really figure out why.
    # So, let's reimplement with a wrapper.
    # The original section we're redoing is by wrapping https://github.com/asweigart/pyautogui/blob/b4255d0be42c377154c7d92337d7f8515fc63234/pyautogui/_pyautogui_osx.py#L238
    # We wrap this by reimplementing https://github.com/asweigart/pyautogui/blob/b4255d0be42c377154c7d92337d7f8515fc63234/pyautogui/__init__.py#L1682

    # Reinforce this through manual pressing and releasing of shift.
    # The inner code of pyautogui does something similar for shift press, but I can't find anywhere that they do
    # shift release.
    # Oddly, it still seems to work OK sometimes, it's just every once in a while it does not. I'm unsure why.
    LOG.info(f"Writing text {text}")
    currently_shifting = False
    write_buffer = ""
    for c in text:
        if pyautogui.isShiftCharacter(c):
            if not currently_shifting:
                # Flush non-shifted characters and start appending shifted ones
                pyautogui.write(write_buffer)
                write_buffer = ""
                # Shift
                pyautogui.keyDown('shift')
            currently_shifting = True
            write_buffer += c
        else:
            if currently_shifting:
                # Flush shifted characters
                pyautogui.write(write_buffer)
                write_buffer = ""
                # Unshift
                pyautogui.keyUp('shift')
            currently_shifting = False
            write_buffer += c
    pyautogui.write(write_buffer)
    pyautogui.keyUp('shift')

def copy():
    with pyautogui.hold('command'):
        pyautogui.press('c')

def paste():
    with pyautogui.hold('command'):
        pyautogui.press('v')

def get_clipboard():
    cp = subprocess.run('pbpaste', capture_output=True)
    return cp.stdout

def set_clipboard(value):
    cp = subprocess.run('pbcopy', capture_output=True, input=value.encode('utf-8'))
    return cp.stdout


def jiggle(coordinates = None, times=5):
    '''
    It seems to help to jiggle the mouse sometimes; this isn't just for mouse enter / mouse move, but the events come 
    so fast that I think some software needs to handle the move event before properly handling click... or something.
    Do this randomly because we don't need determinism in a jiggle.
    '''
    if coordinates != None:
        x = coordinates[0]
        y = coordinates[1]
    else:
        x, y = pyautogui.position()
    for i in range(times):
        jiggle_x = x + random.randint(-3, 3)
        jiggle_y = y + random.randint(-3, 3)
        pyautogui.moveTo((jiggle_x, jiggle_y))
        time.sleep(0.01)
    pyautogui.moveTo((x, y))

class ImageNotFoundException(Exception):
    pass

def find_image(image, confidence=0.6, **kwargs):
    gs = kwargs.pop("grayscale", False)
    image_location = os.path.dirname(__file__) + '/image_targets/' + image
    LOG.info(f"Finding image {image_location}")
    location = pyautogui.locateOnScreen(image_location, grayscale=gs, confidence=confidence, **kwargs)
    if location == None:
        raise ImageNotFoundException(f"Couldn't find image; reference img {image_location}")
    center = pyautogui.center(location)
    retina_center = [c / 2 for c in center]
    LOG.trace(f"Image found at (non-retina coords) {center}; retina coords {retina_center}")
    return retina_center

def last_active_app(previous=1):
    with pyautogui.hold("command"):
        for i in range(previous):
            pyautogui.press('tab')

def center_mouse():
    '''
    Center the mouse on the screen; that's as good a place as any to not hover.
    It might be useful to do some other functions like this because center might not
    always always be the safe place.
    '''
    screen_size = pyautogui.size()
    jiggle((screen_size[0]/2, screen_size[1]/2))

def mouse_near(coordinates, radius=3):
    # Detect if the mouse is within radius (square) pixels of coordinates
    mouse_loc = pyautogui.position()
    return mouse_loc[0] > coordinates[0] - radius and \
            mouse_loc[0] < coordinates[0] + radius and \
            mouse_loc[1] > coordinates[1] - radius and \
            mouse_loc[1] < coordinates[1] + radius

def activate_dock_app_by_image(image):
    center_mouse()
    screen_size = pyautogui.size()
    max_y = int(screen_size.height - (0.2 * screen_size.height)) # bottom 20 percent of the screen
    non_retina_region = (0, max_y*2, screen_size.width * 2, (screen_size.height - max_y)*2)
    retina_center = find_image(image, region=non_retina_region)
    pyautogui.moveTo(retina_center)
    pyautogui.click()

def notify(title="Waiting for a time", text="Some generic message", timeout=1000):
    pyautogui.confirm(title=title, text=text, timeout=timeout)
    last_active_app()
