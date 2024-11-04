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

from PyQt5.QtCore import pyqtSignal, QObject
from .poqueries import PoStationsFullTS

class ROCWorker(QObject):
    progress = pyqtSignal(int)
    current_station = pyqtSignal(str)
    remaining_time_signal = pyqtSignal(int)
    finished = pyqtSignal()
    resultReady = pyqtSignal(object)

    def __init__(self, stats, uuidict, current_text, hours, path, iface):
        super().__init__()
        self.stats = stats
        self.uuidict = uuidict
        self.current_text = current_text
        self.hours = hours
        self.path = path
        self.iface = iface
        self.stat_ts = None

    def run(self):
        """Initiate and run an instance of PoStationsFullTS and forward its signals to the Plugin object"""
        stat_dict = self.stats.timeseries_stations[self.current_text]
        self.stat_ts = PoStationsFullTS(stat_dict, self.uuidict, self.current_text)
        self.stat_ts.progress.connect(self.forwardProgress)
        self.stat_ts.current_station.connect(self.forwardCurrentStation)
        self.stat_ts.remaining_time_signal.connect(self.forwardRemainingTime)
        self.stat_ts.loopThruStations(self.hours)
        self.finished.emit()
        self.resultReady.emit(self.stat_ts)

    def forwardProgress(self, value):
        self.progress.emit(value)

    def forwardCurrentStation(self, string):
        self.current_station.emit(string)

    def forwardRemainingTime(self, seconds):
        self.remaining_time_signal.emit(seconds)