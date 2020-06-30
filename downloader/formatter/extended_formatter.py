#!/usr/bin/env python3
# adapted from https://stackoverflow.com/questions/17848202/python-capitalize-a-word-using-string-format

from string import Formatter
class ExtendedFormatter(Formatter):
    """An extended format string formatter

    Formatter with extended conversion symbols '!U' (uppercase string) and '!L' (lowercase string).
    """
    def convert_field(self, value, conversion):
        """ Extend conversion symbols
        Following additional symbol has been added
        * L: convert to string and lower case
        * U: convert to string and upper case

        default are:
        * s: convert with str()
        * r: convert with repr()
        * a: convert with ascii()
        """

        if conversion == "U":
            return str(value).upper()
        elif conversion == "L":
            return str(value).lower()
        # Do the default conversion or raise error if no matching conversion found
        super(ExtendedFormatter, self).convert_field(value, conversion)

        # return for None case
        return value