import subprocess
from enum import Enum, auto

# https://gist.github.com/martin-ueding/4007035


class ColorCode:
    def __init__(self):
        try:
            self.bold = subprocess.check_output("tput bold".split()).decode()
            self.reset = subprocess.check_output("tput sgr0".split()).decode()

            self.white = subprocess.check_output("tput setaf 7".split()).decode()
            self.cyan = subprocess.check_output("tput setaf 6".split()).decode()
            self.magenta = subprocess.check_output("tput setaf 5".split()).decode()
            self.blue = subprocess.check_output("tput setaf 4".split()).decode()
            self.orange = subprocess.check_output("tput setaf 3".split()).decode()
            self.green = subprocess.check_output("tput setaf 2".split()).decode()
            self.red = subprocess.check_output("tput setaf 1".split()).decode()
            self.black = subprocess.check_output("tput setaf 0".split()).decode()

        except subprocess.CalledProcessError:
            self.bold = ""
            self.reset = ""

            self.white = ""
            self.cyan = ""
            self.magenta = ""
            self.blue = ""
            self.orange = ""
            self.green = ""
            self.red = ""
            self.black = ""


colors = ColorCode()


class TextStyle(Enum):
    Bold = auto()
    Default = auto()


class TextColor(Enum):
    White = auto()
    Cyan = auto()
    Magenta = auto()
    Blue = auto()
    Orange = auto()
    Green = auto()
    Red = auto()
    Black = auto()
