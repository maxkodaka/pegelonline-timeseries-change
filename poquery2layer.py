import json
from qgis.core import QgsJsonUtils, QgsVectorLayer, QgsProject
from PyQt5.QtCore import QTextCodec
from .poquery_classes.poqueries import PoStationsCM

import os
plugin_path = os.path.dirname(__file__)

def addStationLayer(query):

    fcString = json.dumps(query.feature_collection.getDict())

    # using the QgsJsonUtils to create QGIS valid objects
    codec = QTextCodec.codecForName("UTF-8")
    fields = QgsJsonUtils.stringToFields(fcString, codec)
    feats = QgsJsonUtils.stringToFeatureList(fcString, fields, codec)

    # create a QGIS layer and add the data
    vl = QgsVectorLayer('Point?crs=epsg:4326', "Stations " + query.timeseries, "memory")
    dp = vl.dataProvider()
    dp.addAttributes(fields)
    vl.updateFields()

    dp.addFeatures(feats)
    vl.updateExtents()

    vl.setCustomProperty("TS_NAME", query.timeseries)
    vl.loadNamedStyle(os.path.join(plugin_path, "qml", "po_querycm.qml"))

    QgsProject.instance().addMapLayer(vl)

    return vl