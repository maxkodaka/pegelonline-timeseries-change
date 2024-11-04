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


from PyQt5.QtWidgets import QAction, QMessageBox, QDialog, QVBoxLayout, QPushButton, QComboBox, QRadioButton, QButtonGroup, QHBoxLayout, QWidget, QProgressBar, QLabel
from PyQt5.QtCore import QThread
from .pograph import PoGraph
from .poquery_classes.poqueries import PoStationsTS, PoStationsCM, PoStationsDict, PoStationsFullTS
from .poquery_classes.rocworker import ROCWorker
from.poquery2layer import addStationLayer
import os
from pprint import pprint


class Plugin:

    def __init__(self, iface):
        self.iface = iface
        self.path = os.path.dirname(__file__)
        self.thread = None
        self.worker = None
        self.progressBar = None

    def initGui(self):
        self.action = QAction('tsDeriv', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

        self.first_start = True

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def run(self):
        if self.first_start == True:
            self.first_start = False

            self.stats = PoStationsTS()
            self.stats.read()
            self.ts_dict = self.stats.getTimeseriesSimple()
            self.stats.linkShortLongNames()

            # Get the station uuids
            self.statdictobj = PoStationsDict()
            self.uuidict = self.statdictobj.read()

            self.dlg = QDialog()
            layout = QVBoxLayout(self.dlg)

            # Timeseries Dropdown List
            self.cb = QComboBox()
            # Sort timeseries into the combobox in order of the number of stations per timeseries
            #ts_dict_sorted_keys = sorted(self.ts_dict, key = lambda x: len(self.ts_dict[x]), reverse = True)
            ts_dict_sorted_keys = sorted(self.stats.timeseries_stations, key = lambda x: len(self.stats.timeseries_stations[x]), reverse = True)
            for k in ts_dict_sorted_keys:
                self.cb.addItem(self.stats.ts_shortname_longname[k])
            self.cb.currentIndexChanged.connect(self.selectionchange)
            layout.addWidget(self.cb)

            # Graph
            self.graph = PoGraph(self.stats.ts_longname_shortname, ts_combobox=self.cb)
            self.selectionchange(0)
            layout.addWidget(self.graph)

            # Load Current measurement layer button
            btnLoad = QPushButton('Load Current Measurement Layer')
            btnLoad.clicked.connect(self.load)
            layout.addWidget(btnLoad)

            # Load Rate of Change measurement layer button
            self.btnLoadROC = QPushButton('Load Rate of Change Layer')
            self.btnLoadROC.clicked.connect(self.loadROC)
            layout.addWidget(self.btnLoadROC)

            # Radio Buttons for Rate of Change time frame selection
            self.radioBtn3h = QRadioButton('3 hours')
            self.radioBtn3h.hours = 3
            self.radioBtn6h = QRadioButton('6 hours')
            self.radioBtn6h.hours = 6
            self.radioBtn12h = QRadioButton('12 hours')
            self.radioBtn12h.hours = 12
            self.radioBtn24h = QRadioButton('24 hours')
            self.radioBtn24h.hours = 24

            self.radioBtn6h.setChecked(True)

            # Button Group for Radio Buttons
            self.timeButtonGroup = QButtonGroup()
            self.timeButtonGroup.addButton(self.radioBtn3h)
            self.timeButtonGroup.addButton(self.radioBtn6h)
            self.timeButtonGroup.addButton(self.radioBtn12h)
            self.timeButtonGroup.addButton(self.radioBtn24h)

            timeBtnLayout = QHBoxLayout()
            timeBtnLayout.addWidget(self.radioBtn3h)
            timeBtnLayout.addWidget(self.radioBtn6h)
            timeBtnLayout.addWidget(self.radioBtn12h)
            timeBtnLayout.addWidget(self.radioBtn24h)
            timeBtnWidget = QWidget()
            timeBtnWidget.setLayout(timeBtnLayout)

            layout.addWidget(timeBtnWidget)
            
            # Progress Bar
            self.progressBar = QProgressBar()
            self.progressBar.setMaximum(100)
            self.progressBar.hide()
            layout.addWidget(self.progressBar)

            # Remaining Time label for progress bar
            self.timeRemainingLabel = QLabel()
            self.timeRemainingLabel.hide()
            layout.addWidget(self.timeRemainingLabel)

            # Cancel button for ROC processing
            self.btnCancel = QPushButton('Cancel')
            self.btnCancel.clicked.connect(self.cancel)
            self.btnCancel.hide()
            layout.addWidget(self.btnCancel)

            # Close button
            btnClose = QPushButton('Close')
            btnClose.clicked.connect(self.dlg.close)
            layout.addWidget(btnClose)


        self.dlg.show()
        self.dlg.exec_()

    def load(self):
        """Load the current timeseries values as a layer"""
        ts_shortname=self.stats.ts_longname_shortname[self.cb.currentText()]
        stat_ts = PoStationsCM(ts_shortname)
        stat_ts.read()
        lyr = addStationLayer(stat_ts)

        self.iface.setActiveLayer(lyr)
        self.iface.zoomToActiveLayer()

    def loadROC(self):
        """Create a worker and load the layers for current rate of change in a separate thread"""
        self.progressBar.show()
        self.timeRemainingLabel.show()
        self.btnCancel.show()
        self.btnLoadROC.setEnabled(False)
        self.thread = QThread()
        self.worker = ROCWorker(
                                    self.stats,
                                    self.uuidict,
                                    self.stats.ts_longname_shortname[self.cb.currentText()],
                                    self.timeButtonGroup.checkedButton().hours,
                                    self.path,
                                    self.iface
                                   )

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.progress.connect(self.updateProgress)
        self.worker.current_station.connect(self.displayProcessingStation)
        self.worker.remaining_time_signal.connect(self.displayRemainingTime)
        self.worker.resultReady.connect(self.addLayer)

        self.progressBar.setValue(0)
        self.thread.start()

    def addLayer(self, stat_ts):
        """Add the feature collection returned by ROCWorker as a layer"""
        self.progressBar.setFormat('Adding layer...')
        lyr = addStationLayer(stat_ts)
        qmlpath = os.path.join(self.path, 'qml', 'po_stations_fullTS_units.qml')
        lyr.loadNamedStyle(qmlpath)
        iface = self.iface
        iface.setActiveLayer(lyr)
        iface.zoomToActiveLayer()
        self.btnLoadROC.setEnabled(True)
        self.progressBar.setFormat('Finished!')
        self.btnCancel.hide()
        self.timeRemainingLabel.hide()

    def selectionchange(self, i):
        ts_shortname = self.stats.ts_longname_shortname[self.cb.currentText()]
        self.graph.setStations(self.ts_dict[ts_shortname])

    def updateProgress(self, value):
        self.progressBar.setValue(value)

    def displayProcessingStation(self, string):
        self.progressBar.setFormat(f'Currently processing: {string}')

    def displayRemainingTime(self, seconds):
        mm = seconds // 60
        ss = seconds % 60
        self.timeRemainingLabel.setText(f'Estimated time remaining: {mm:02}:{ss:02}')

    def cancel(self):
        self.worker.stat_ts.is_cancelled = True
        self.btnCancel.hide()
        self.progressBar.hide()
        self.timeRemainingLabel.hide()
