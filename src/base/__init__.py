import logging.config
import yaml
import re
 
## SELENIUM SETUP
from selenium import webdriver 
from selenium.webdriver.common.by import By
# create webdriver object 
driver = webdriver.Firefox() 
    
# set implicit wait time
driver.implicitly_wait(10) # seconds

from selenium.webdriver.common.action_chains import ActionChains

##  LOGGING SETUP
class ConsoleFormatter(logging.Formatter):


    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    COLOR_TABLE = [
        'black',
        'maroon',
        'green',
        'olive',
        'navy',
        'purple',
        'teal',
        'silver',
        'grey',
        'red',
        'lime',
        'yellow',
        'blue',
        'fuchsia',
        'aqua',
        'white',
        'grey0',
        'navyblue',
        'darkblue',
        'blue3',
        'blue3',
        'blue1',
        'darkgreen',
        'deepskyblue4',
        'deepskyblue4',
        'deepskyblue4',
        'dodgerblue3',
        'dodgerblue2',
        'green4',
        'springgreen4',
        'turquoise4',
        'deepskyblue3',
        'deepskyblue3',
        'dodgerblue1',
        'green3',
        'springgreen3',
        'darkcyan',
        'lightseagreen',
        'deepskyblue2',
        'deepskyblue1',
        'green3',
        'springgreen3',
        'springgreen2',
        'cyan3',
        'darkturquoise',
        'turquoise2',
        'green1',
        'springgreen2',
        'springgreen1',
        'mediumspringgreen',
        'cyan2',
        'cyan1',
        'darkred',
        'deeppink4',
        'purple4',
        'purple4',
        'purple3',
        'blueviolet',
        'orange4',
        'grey37',
        'mediumpurple4',
        'slateblue3',
        'slateblue3',
        'royalblue1',
        'chartreuse4',
        'darkseagreen4',
        'paleturquoise4',
        'steelblue',
        'steelblue3',
        'cornflowerblue',
        'chartreuse3',
        'darkseagreen4',
        'cadetblue',
        'cadetblue',
        'skyblue3',
        'steelblue1',
        'chartreuse3',
        'palegreen3',
        'seagreen3',
        'aquamarine3',
        'mediumturquoise',
        'steelblue1',
        'chartreuse2',
        'seagreen2',
        'seagreen1',
        'seagreen1',
        'aquamarine1',
        'darkslategray2',
        'darkred',
        'deeppink4',
        'darkmagenta',
        'darkmagenta',
        'darkviolet',
        'purple',
        'orange4',
        'lightpink4',
        'plum4',
        'mediumpurple3',
        'mediumpurple3',
        'slateblue1',
        'yellow4',
        'wheat4',
        'grey53',
        'lightslategrey',
        'mediumpurple',
        'lightslateblue',
        'yellow4',
        'darkolivegreen3',
        'darkseagreen',
        'lightskyblue3',
        'lightskyblue3',
        'skyblue2',
        'chartreuse2',
        'darkolivegreen3',
        'palegreen3',
        'darkseagreen3',
        'darkslategray3',
        'skyblue1',
        'chartreuse1',
        'lightgreen',
        'lightgreen',
        'palegreen1',
        'aquamarine1',
        'darkslategray1',
        'red3',
        'deeppink4',
        'mediumvioletred',
        'magenta3',
        'darkviolet',
        'purple',
        'darkorange3',
        'indianred',
        'hotpink3',
        'mediumorchid3',
        'mediumorchid',
        'mediumpurple2',
        'darkgoldenrod',
        'lightsalmon3',
        'rosybrown',
        'grey63',
        'mediumpurple2',
        'mediumpurple1',
        'gold3',
        'darkkhaki',
        'navajowhite3',
        'grey69',
        'lightsteelblue3',
        'lightsteelblue',
        'yellow3',
        'darkolivegreen3',
        'darkseagreen3',
        'darkseagreen2',
        'lightcyan3',
        'lightskyblue1',
        'greenyellow',
        'darkolivegreen2',
        'palegreen1',
        'darkseagreen2',
        'darkseagreen1',
        'paleturquoise1',
        'red3',
        'deeppink3',
        'deeppink3',
        'magenta3',
        'magenta3',
        'magenta2',
        'darkorange3',
        'indianred',
        'hotpink3',
        'hotpink2',
        'orchid',
        'mediumorchid1',
        'orange3',
        'lightsalmon3',
        'lightpink3',
        'pink3',
        'plum3',
        'violet',
        'gold3',
        'lightgoldenrod3',
        'tan',
        'mistyrose3',
        'thistle3',
        'plum2',
        'yellow3',
        'khaki3',
        'lightgoldenrod2',
        'lightyellow3',
        'grey84',
        'lightsteelblue1',
        'yellow2',
        'darkolivegreen1',
        'darkolivegreen1',
        'darkseagreen1',
        'honeydew2',
        'lightcyan1',
        'red1',
        'deeppink2',
        'deeppink1',
        'deeppink1',
        'magenta2',
        'magenta1',
        'orangered1',
        'indianred1',
        'indianred1',
        'hotpink',
        'hotpink',
        'mediumorchid1',
        'darkorange',
        'salmon1',
        'lightcoral',
        'palevioletred1',
        'orchid2',
        'orchid1',
        'orange1',
        'sandybrown',
        'lightsalmon1',
        'lightpink1',
        'pink1',
        'plum1',
        'gold1',
        'lightgoldenrod2',
        'lightgoldenrod2',
        'navajowhite1',
        'mistyrose1',
        'thistle1',
        'yellow1',
        'lightgoldenrod1',
        'khaki1',
        'wheat1',
        'cornsilk1',
        'grey100',
        'grey3',
        'grey7',
        'grey11',
        'grey15',
        'grey19',
        'grey23',
        'grey27',
        'grey30',
        'grey35',
        'grey39',
        'grey42',
        'grey46',
        'grey50',
        'grey54',
        'grey58',
        'grey62',
        'grey66',
        'grey70',
        'grey74',
        'grey78',
        'grey82',
        'grey85',
        'grey89',
        'grey93']

    def __init__(self, fmt):
        self.fmt = fmt

    @staticmethod
    def term_256_color(text, fg_color_name = None, bg_color_name=None, underline=False, strikethrough=False):
        color_format_str = ""
        if fg_color_name:
            color_format_str = color_format_str + u'\u001b[38;5;' + str(ConsoleFormatter.COLOR_TABLE.index(fg_color_name)) + u'm'
        if bg_color_name:
            color_format_str = color_format_str + u'\u001b[48;5;' + str(ConsoleFormatter.COLOR_TABLE.index(bg_color_name)) + u'm'
        color_format_str += text
        color_format_str += u'\u001b[0m' #Always reset the string just in case
        return color_format_str

    @staticmethod
    def colorize_levelname(record, token):
        # Colorize on levelno instead to handle future names (will show up with different level name but same
        # color as next highest level
        if record.levelno < logging.DEBUG:
            return ConsoleFormatter.term_256_color(token, 'yellow4', 'grey11')
        if record.levelno == logging.DEBUG:
            return ConsoleFormatter.term_256_color(token, 'darkgreen', 'grey11')
        elif record.levelno <= logging.INFO:
            return ConsoleFormatter.term_256_color(token, 'navy', )
        elif record.levelno <= logging.WARN:
            return ConsoleFormatter.term_256_color(token, 'orange1')
        elif record.levelno <= logging.ERROR:
            return ConsoleFormatter.term_256_color(token, 'maroon')
        elif record.levelno <= logging.CRITICAL:
            return ConsoleFormatter.term_256_color(token, 'red', 'silver')
        else:
            return token

    @staticmethod
    def colorize_timestamp(record, token):
        # Colorize based on last digit of timestamp
        ts_ones_value = int(record.created) % 10
        # Evens odds
        if ts_ones_value % 2 == 0:
            return ConsoleFormatter.term_256_color(token, 'grey30', 'grey50')
        else:
            return ConsoleFormatter.term_256_color(token, 'grey50', 'grey30')

    @staticmethod
    def colorize_logger_name(record, token):
        # fast and dumb stable hash: sum and mod the byte values
        btes = record.name.encode(encoding='UTF-8')
        return ConsoleFormatter.term_256_color(token, ConsoleFormatter.COLOR_TABLE[sum(btes)% 16], 'grey11')

    @staticmethod
    def colorize_message_params(message, token):
        pass

    def format(self, record):
        """
        This got messy quickly.
        Basically the goal is to color-code the messages such that they are easier to read as a human being (in the console).
        I want to do this programmatically, e.g. debug is one color, warning is another.
        That means that we need to have a dynamic format string that changes based on the record. Python's logging doesn't really
        support this / make it easy (because it can be expensive as a general purpose functionality and crosses a division of
        reponsibilities with the design of the built-in logger).
        I tried with a custom record (putting the console color string in the record itself) but the string formatting will
        truncate it including formatting strings. I have to munge the format string itself to make this work to put in the 
        format escapes just outside of the formatted field. That means a little more parsing work
        to make this formatter "magic" with known format string constants like "name" and "levelname"
        """
        regex = r'(?P<token>%(\(\w+\))*[#0 \-\+]*[0-9\.]*[diouxXeEfFgGcrsa])'
        dynamic_format = self.fmt
        tokens = map(lambda t: t[0], re.findall(regex, dynamic_format))
        for token in tokens:
            if token.find("levelname") > 0:
                dynamic_format = dynamic_format.replace(token, self.colorize_levelname(record, token))
            elif token.find("asctime") > 0:
                dynamic_format = dynamic_format.replace(token, self.colorize_timestamp(record, token))
            elif token.find("name") > 0:
                dynamic_format = dynamic_format.replace(token, self.colorize_logger_name(record, token))

        formatter = logging.Formatter(dynamic_format)
        return formatter.format(record)

logConfig = """
version: 1
disable_existing_loggers: true
formatters:
  simple:
    format: '[%(asctime)24.24s - %(name)-20.20s - %(levelname)5.5s] %(message)s'
  colored_console:
    format: '[%(asctime)24.24s - %(name)-20.20s - %(levelname)5.5s] %(message)s'
    '()': base.ConsoleFormatter
handlers:
  console:
    class: logging.StreamHandler
    level: TRACE
    formatter: colored_console
    stream: ext://sys.stdout
  file:
    class: logging.FileHandler
    level: TRACE
    filename: ../logs/log
root:
  level: TRACE
  handlers: [console,file]
"""


# Taken from https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/35804945#35804945
def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present 

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)

addLoggingLevel("TRACE", logging.DEBUG - 5)


logging.config.dictConfig(yaml.load(logConfig, Loader=yaml.FullLoader))

# Test out logging level printing / report to terminal what they look like
LOG = logging.getLogger("base.LOG")
LOG.trace("This is a TRACE message")
LOG.debug("This is a DEBUG message")
LOG.info("This is a INFO message")
LOG.warning("This is a WARNING message")
LOG.error("This is a ERROR message")
LOG.critical("This is a CRITICAL message")

# Add an assert
ASSERT_LOG= logging.getLogger("ASSERT")
# This can be called with no arguments to log and trigger a debugger
def ASSERT(condition_that_should_be_true=False, message="Unspecified", debug_on_fail=True):
    if condition_that_should_be_true:
        return True
    LOG.critical(f"Failed assert: {message}")
    if debug_on_fail:
        import pdb; pdb.set_trace()
    return condition_that_should_be_true # False by this point - it's not in fact true.



# BASE CLASSES AND FUNCTIONALITY
import argparse
class CommandParser(argparse.ArgumentParser):

    class ParseError(Exception):
        pass

    # TODO: bring this into an ASSERT when I'm sure that handles stack traces usefully.
    def error(self, message):
        LOG.critical(message)
        raise CommandParser.ParseError(message)

class AutomationCommandBase:
    name = "INHERITORS_SHOULD_OVERRIDE"

    parser = None
    #Override using argparse like this
    #parser = CommandParser(prog = name, description=f'{name} command')
    #parser.add_argument("uri", metavar='URI', type=str)


    def __init__(self, command_args):
        self._argstr = command_args
        self._args = self.__class__.parser.parse_args(command_args)
        
    def __str__(self):
        return f"{self.__class__.name}: {self._args}"

    @staticmethod
    def element_by_xpath(xpath):
        elements = AutomationCommandBase.elements_by_xpath(xpath)
        if not ASSERT(len(elements) == 1, f"Found more than one element with xpath {xpath}"):
            return None
        return elements[0]

    @staticmethod
    def elements_by_xpath(xpath):
        elements = driver.find_elements(By.XPATH, xpath)
        if len(elements) == 0:
            LOG.info("We didn't find any element")
            return None
        return elements
