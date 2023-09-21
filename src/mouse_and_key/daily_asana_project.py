import os
import time
import datetime
import random
import pyautogui
import clicky_scripts.util as util
import logging
import python_logging_base
from python_logging_base import ASSERT

LOG = logging.getLogger("daily_start")
LOG.setLevel(logging.TRACE)

class DailyAsanaProject:
    '''
    Clone and create a new project of the day in Asana.
    '''

    text_date_format = "%m/%d/%Y (%a) Daily"
    wait_time = 5

    @staticmethod
    def new_tab(address):
        LOG.info(f"Opening tab at {address}")
        with pyautogui.hold('command'):
            pyautogui.press('t')
        time.sleep(0.25)
        # Hack. For some reason the hold keys get wacked and shift seems pressed.
        DailyAsanaProject.write_text(address)
        pyautogui.press("enter")

    @staticmethod
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

    def __init__(self, date = datetime.datetime.today(), qt_app = None):
        self._date = date
        self.text_date = self._date.strftime(DailyAsanaProject.text_date_format)
        self._qt_app = qt_app

    def info(self, message):
        # Just a little simplifying this frequent function
        LOG.debug(message)
        self._qt_app.inform(message)

    def info_wait(self, message, wait_scale = 1):
        wait = DailyAsanaProject.wait_time * wait_scale
        self.info(f"{message} ({wait} seconds)")
        time.sleep(wait)

    def jiggle(self, coordinates):
        '''
        It seems to help to jiggle the mouse sometimes; this isn't just for mouse enter / mouse move, but the events come 
        so fast that I think some software needs to handle the move event before properly handling click... or something.
        Do this randomly because we don't need determinism in a jiggle.
        '''
        x = coordinates[0]
        y = coordinates[1]
        for i in range(10):
            jiggle_x = x + random.randint(-3, 3)
            jiggle_y = y + random.randint(-3, 3)
            pyautogui.moveTo((jiggle_x, jiggle_y))
            time.sleep(0.01)
        pyautogui.moveTo((x, y))

    def instantiate_template(self):
        self.info("Instantiating template...")
        retina_center = util.find_image("asana_use_template.png")
        self.jiggle(retina_center)
        pyautogui.click()
        self.info_wait("Instantiating template", 0.5)
        LOG.info("Creating project for {self.text_date}")
        DailyAsanaProject.write_text(self.text_date)
        # Tab 3 times to get to the date picker
        for i in range(3):
            pyautogui.press("tab")
        # Backspace a bunch
        for i in range(10):
            pyautogui.press("backspace")
        date_picker_date_format = self._date.strftime("%m/%d/%Y")
        DailyAsanaProject.write_text(date_picker_date_format)
        pyautogui.press("enter")
        retina_center = util.find_image("asana_create_project.png")
        self.jiggle(retina_center)
        pyautogui.click()

    def add_to_portfolio(self):
        self.info("Adding project to portfolio")
        self.new_tab("https://app.asana.com/0/portfolio/1203786245754929/list")
        self.info_wait(f"Loading portfolio")
        self.info(f"Adding work")
        retina_center = util.find_image("asana_add_work.png", 0.6)
        self.jiggle(retina_center)
        pyautogui.click()
        DailyAsanaProject.write_text(self.text_date)
        self.info_wait(f"Waiting for project to appear in typeahead", 0.5)
        pyautogui.press("enter")

    def set_project_color(self):
        # Find the new project by its icon
        self.info_wait("Opening project")
        retina_center = util.find_image("asana_new_project_icon.png", 0.6)
        self.jiggle(retina_center)
        pyautogui.click()
        time.sleep(1) #Load page; should be quick
        # Find the icon *again*
        self.info("Setting color")
        retina_center = util.find_image("asana_new_project_icon.png", 0.6)
        self.jiggle(retina_center)
        pyautogui.click()
        # OK, at this point we have the color picker out.
        # Let's choose the right color based on the day.
        # Remember, 0=monday.
        day_of_week = self._date.weekday()
        def click_color(day):
            retina_center = util.find_image(f"asana_{day}_color.png", 0.98)
            self.jiggle(retina_center)
            pyautogui.click()

        if day_of_week == 0:
            click_color("monday")
        elif day_of_week == 1:
            click_color("tuesday")
        elif day_of_week == 2:
            click_color("wednesday")
        elif day_of_week == 3:
            click_color("thursday")
        elif day_of_week == 4:
            click_color("friday")
        elif day_of_week == 5:
            click_color("saturday")
        elif day_of_week == 6:
            click_color("sunday")

    def daystart(self):
        self.info("Asana daystart")
        util.activate_dock_app_by_image("chrome_in_dock.png")
        self.new_tab("https://app.asana.com/0/project-templates/1203786245754952/list")
        self.info_wait(f"Loading Asana")
        self.instantiate_template()
        # OK, we have a new project! Add it to the portfolio
        self.add_to_portfolio()
        self.set_project_color()
        self.info("Ready for next action!")

    def archive_project(self):
        self.info("Archiving project")
        retina_center = util.find_image("project_caret.png", 0.8)
        self.jiggle(retina_center)
        pyautogui.click()
        retina_center = util.find_image("archive_menu_item.png", 0.8)
        self.jiggle(retina_center)
        pyautogui.click()

    def gray_out_project_color_and_change_icon(self):
        self.info("Graying out and setting complete icon")
        # Gray out the project color
        retina_center = util.find_image("asana_new_project_icon.png", 0.6, grayscale=True)
        self.jiggle(retina_center)
        pyautogui.click()
        retina_center = util.find_image(f"asana_no_day_color.png", 0.98)
        self.jiggle(retina_center)
        pyautogui.click()
        #Click out of the dialog to clean up
        retina_center = util.find_image("asana_new_project_icon.png", 0.6, grayscale=True)
        pyautogui.moveTo((retina_center[0] - 30, retina_center[1]))
        pyautogui.click()
        # Set the icon to the check mark icon
        retina_center = util.find_image("asana_new_project_icon.png", 0.6, grayscale=True)
        self.jiggle(retina_center)
        pyautogui.click()
        retina_center = util.find_image(f"check_mark_project_icon.png", 0.9)
        self.jiggle(retina_center)
        pyautogui.click()

    def unfavorite(self):
        # TODO: add logic to test if this is actually favorited or fail if it's not (empty star)
        retina_center = util.find_image(f"check_mark_project_icon.png", 0.9)
        self.jiggle(retina_center)
        pyautogui.click()


    def dayend(self):
        # Assume starting with tab open.
        util.activate_dock_app_by_image("chrome_in_dock.png")
        LOG.info("Assume we're starting with the tab open")
        LOG.todo("Have some way of reading/ocr-ing text to find on page? Hmm...")
        self.gray_out_project_color_and_change_icon()
        self.archive_project()
        self.info("Ready for next action!")

