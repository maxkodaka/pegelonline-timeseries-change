#-----------------------------------------------------------
# Copyright (C) 2024 Max Kodaka
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

from .plugin import Plugin

def classFactory(iface):
    return Plugin(iface)
