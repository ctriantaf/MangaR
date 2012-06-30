# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012 Chris Triantafillis <christriant1995@gmail.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

# This is your preferences dialog.
#
# Define your preferences in
# data/glib-2.0/schemas/net.launchpad.mangar.gschema.xml
# See http://developer.gnome.org/gio/stable/GSettings.html for more info.

from gi.repository import Gio # pylint: disable=E0611

import gettext
from gettext import gettext as _
gettext.textdomain('mangar')

import logging
logger = logging.getLogger('mangar')

from mangar_lib.PreferencesDialog import PreferencesDialog

class PreferencesMangarDialog(PreferencesDialog):
    __gtype_name__ = "PreferencesMangarDialog"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the preferences dialog"""
        super(PreferencesMangarDialog, self).finish_initializing(builder)

        # Bind each preference widget to gsettings
        settings = Gio.Settings("net.launchpad.mangar")
        widget = self.builder.get_object('collection_folder_entry')
        widget2 = self.builder.get_object('output_folder_entry')
        settings.bind("collectionfolder", widget, "text", Gio.SettingsBindFlags.DEFAULT)
		settings.bind("outputfolder", widget2, "text", Gio.SettingsBindFlags.DEFAULT)
        
        # Code for other initialization actions should be added here.
