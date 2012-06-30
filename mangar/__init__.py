# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import optparse
import os

import gettext
from gettext import gettext as _
gettext.textdomain('mangar')

from gi.repository import Gtk # pylint: disable=E0611

from mangar import MangarWindow

from mangar_lib import set_up_logging, get_version

def parse_options():
    """Support for command line options"""
    parser = optparse.OptionParser(version="%%prog %s" % get_version())
    parser.add_option(
        "-v", "--verbose", action="count", dest="verbose",
        help=_("Show debug messages (-vv debugs mangar_lib also)"))
    (options, args) = parser.parse_args()

    set_up_logging(options)

def check_files():
	"""Check folder"""
	home = os.getenv('HOME')
	program_folder = home + "/.config/mangar/"
	collection_file = program_folder + "collection"
	if not os.path.exists(program_folder):
		os.mkdir(program_folder, 0700)
	try:
		f = open(collection_file, 'rb')
		f.close()
    except IOError:
        f = open(collection_file, 'wb')
        f.close()

def main():
    'constructor for your class instances'
    parse_options()
	check_files()
	
    # Run the application.    
    window = MangarWindow.MangarWindow()
    window.show()
    Gtk.main()
