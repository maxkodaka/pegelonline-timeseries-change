import sys
from qgis.PyQt.QtWidgets import QApplication, QWidget, QComboBox, QVBoxLayout, QLabel
from qgis.PyQt import QtGui
from .poquery_classes.urlreader import Urlreader, quote
from .poquery_classes import poBaseURL
from .poquery_classes.poqueries import PoStationsCW

class PoGraph(QWidget):

    def __init__(self, ts_longname_shortname, ts_combobox, parent=None):
        super().__init__(parent)
        self.initUI()
        self.ts_combobox = ts_combobox
        self.ts_longname_shortname = ts_longname_shortname

    def initUI(self):
        self.verticalLayout = QVBoxLayout(self)
        self.station_comboBox = QComboBox()
        self.station_comboBox.currentIndexChanged.connect(self.doLoadGraph)
        self.lbGraph = QLabel()
        self.verticalLayout.addWidget(self.station_comboBox)
        self.verticalLayout.addWidget(self.lbGraph)

    def doLoadGraph(self):
        station_shortname = quote(self.station_comboBox.currentText())
        ts_shortname = self.ts_longname_shortname[self.ts_combobox.currentText()]
        ur = Urlreader(poBaseURL + "/stations/%s/%s/measurements.png?start=P01D" % (station_shortname, ts_shortname))

        img_data = ur.getDataResponse()
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(img_data)
        self.lbGraph.setPixmap(pixmap)
        self.lbGraph.resize(pixmap.width(), pixmap.height())

    # Interface to set a list of stations to choose from
    def setStations(self, stations=[]):
        self.station_comboBox.clear()
        for s in sorted(stations):
            self.station_comboBox.addItem(s)

        self.station_comboBox.setCurrentIndex(0)