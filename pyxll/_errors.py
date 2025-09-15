"""
Copyright (c) 2009-2012, All Rights Reserved, http://www.pyxll.com/

THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
PARTICULAR PURPOSE.
"""

class Error(Exception):
    """Raised from commands with an error message"""
    pass

class Help(Exception):
    """Raised from commands in order to print the help message"""
    pass