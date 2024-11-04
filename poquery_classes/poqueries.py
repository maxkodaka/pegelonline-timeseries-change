import json
from pprint import pprint
from . import poBaseURL
from .geojs import GjFeatureCollection, GjFeature
import pandas as pd
from .urlreader import Urlreader
from PyQt5.QtCore import QObject, pyqtSignal, QTime

class PoQuery:
    def __init__(self):
        self.keys = []                  
        self.query = ""              
        self.feature_collection = None


    def convert2Feature(self, station):
        pass

    def read(self):
        pass

    def write(self):
        pass

    def getIndexTS(self, station, tshort):
        """workaround function for using URL-parameter hasTimeseries"""
        index=0
        for ts in station['timeseries']:
            if ts['shortname'] == tshort:
                break
            else:
                index+=1
        return index


class PoStations(PoQuery):
    def __init__(self):
        super(PoStations, self).__init__()
        self.query = poBaseURL + "stations.json"
        self.keys = ["uuid", "number", "shortname", "longname", "km", "agency",
        "longitude", "latitude", "water"]

    def convert2Feature(self, station):
        """Convert json data into a geojson feature"""
        feat = GjFeature()
        try:
            feat.setCoordinates(station['longitude'], station['latitude'])
        except KeyError as e:
            print("Station can't be added: %s"%e)
            return None

        # set properties
        for k in self.keys:
            if k != 'water':
                prop = {k : station.get(k, None)}
            else:
                prop = {k : station.get(k, {'longname': 'unknown'})['longname']}
            feat.setProperty(prop)

        return feat

    def read(self):
        """Query the API and convert json data to a geojson feature collection"""
        self.feature_collection = GjFeatureCollection()

        ur = Urlreader(self.query)
        jsdata = ur.getJsonResponse()

        for stat in jsdata:
            feat = self.convert2Feature(stat)
            if feat:
                self.feature_collection.addFeature(feat)

    def write(self, filename):
        self.feature_collection.write(filename)



class PoStationsCW(PoStations):
    def __init__(self):
        super(PoStationsCW, self).__init__()
        ## new parameter hasTimeseries is used here
        self.query = poBaseURL + "stations.json?includeTimeseries=true&?hasTimeseries=W&includeCurrentMeasurement=true"
        self.keys_cw = ["value", "timestamp", "stateMnwMhw", "stateNswHsw"]

    def convert2Feature(self, station):
        """Convert json data into a geojson feature"""
        feat = super(PoStationsCW, self).convert2Feature(station)
        if not feat:
            return None
        
        index = self.getIndexTS(station, 'W')

        for k in self.keys_cw:
            w = station['timeseries'][index]['currentMeasurement']
            prop = {k : w.get(k, None)}
            feat.setProperty(prop)

        return feat


class PoStationsCwCv(PoStationsCW):
    def __init__(self):
        super(PoStationsCwCv, self).__init__()
        self.query = poBaseURL + "stations.json?includeTimeseries=true&hasTimeseries=W&includeCurrentMeasurement=true&includeCharacteristicValues=true"
        self.keys_cv = ["shortname", "longname", "unit", "value"]
        self.shortnames_cv = ['MW', 'MHW', 'MNW', 'HSW', 'HHW', 'NNW']

    def convert2Feature(self, station):
        """Convert json data into a geojson feature"""
        feat = super(PoStationsCwCv, self).convert2Feature(station)
        if not feat:
            return None
            
        index = self.getIndexTS(station, 'W')

        for cv in station['timeseries'][index]['characteristicValues']:
            if cv['shortname'] in self.shortnames_cv:

                for k in self.keys_cv:
                    ## create a field name by combining shortnames_cv and keys_cv
                    ## like in the example file: MHW_value, MNW_value ...
                    fld_name = "%s_%s" % (cv['shortname'], k)
                    ## create a property: like we usually did:
                    prop = {fld_name : cv.get(k, None)}
                    feat.setProperty(prop)

        return feat


class PoStationsTS(PoStations):
    """New query class for accessing all timeseries"""
    def __init__(self):
        super(PoStationsTS, self).__init__()
        self.query = poBaseURL + "stations.json?includeTimeseries=true"
        self.timeseries_stations = {}
        self.stations_timeseries = {}
        self.ts_shortname_longname = {}
        self.ts_longname_shortname = {}

    def convert2Feature(self, station):
        """Convert json data into a geojson feature"""
        feat = super(PoStationsTS, self).convert2Feature(station)

        if feat:
            self.updateTimeseries(station)
            self.updateStations(station)

        return feat

    def updateTimeseries(self, station):
        """Populates the dictionary specifying which stations exist for which timeseries"""
        for ts in station['timeseries']:
            if ts['shortname'] in self.timeseries_stations.keys():
                # existing timeseries, adding another station
                self.timeseries_stations[ts['shortname']]['stations'].update(
                            {station['shortname']: {
                                'unit': ts['unit'],
                                'equidistance': ts['equidistance']
                                }
                            }
                        )

            else:
                # new timeseries, adds first station
                self.timeseries_stations[ts['shortname']] = {
                            'longname': ts['longname'],
                            'stations': {station['shortname']: {
                                'unit': ts['unit'],
                                'equidistance': ts['equidistance']
                                }
                            }
                        }
        
    def getTimeseriesSimple(self):
        result = {}
        for k in self.timeseries_stations.keys():
            stlist = [st for st in self.timeseries_stations[k]['stations']]
            result[k] = stlist

        return result


    def linkShortLongNames(self):
        """Creates dictionaries for converting shortname to longname and vice versa. Must be used after read()."""
        for k in self.timeseries_stations.keys():
            self.ts_shortname_longname[k] = self.timeseries_stations[k]['longname']
        self.ts_longname_shortname = {v: k for k, v in self.ts_shortname_longname.items()}


    def updateStations(self, station):
        """Populates the dictionary specifying which timeseries exist for which stations"""

        # add station shortname as key
        self.stations_timeseries.update({station['shortname']:[]})
        # add timeseries for that station
        for ts in station['timeseries']:
            self.stations_timeseries[station['shortname']].append(ts['shortname'])


    def getStationsSimple(self):
        return self.stations_timeseries


class PoStationsCM(PoStations):
    """Query class to get current measurements for a specific timeseries"""
    def __init__(self, timeseries):
        super(PoStationsCM, self).__init__()
        self.query = poBaseURL + "stations.json?includeTimeseries=true&includeCurrentMeasurement=true&hasTimeseries=%s"%timeseries
        self.keys_unit = ["unit"]
        self.keys_cm = ["value", "timestamp"]
        self.timeseries = timeseries

    def convert2Feature(self, station):
        feat = super(PoStationsCM, self).convert2Feature(station)
        if not feat:
            return None

        index = self.getIndexTS(station, self.timeseries)

        for k in self.keys_cm:
            w = station['timeseries'][index]['currentMeasurement']
            prop = {k : w.get(k, None)}
            feat.setProperty(prop)

        prop = {'unit': station['timeseries'][index]['unit']}
        feat.setProperty(prop)

        return feat


class PoStationsDict(PoQuery):
    """Query class to get a dictionary of station name:uuid for querying individual station time series"""
    def __init__(self):
        super(PoStationsDict, self).__init__()
        self.query = poBaseURL + "stations.json"
        self.uuidict = {}
        self.keys = ["uuid", "number", "longname", "km", "agency",
        "longitude", "latitude"]

    def read(self):
        ur = Urlreader(self.query)
        jsdata = ur.getJsonResponse()

        for stat in jsdata:
            self.uuidict[stat['shortname']] = {}

            for k in self.keys:
                self.uuidict[stat['shortname']][k] = stat.get(k,'None')

        return self.uuidict
    

class PoStationsFullTS(PoStations, QObject):
    """Query class to get the full timeseries for each station"""
    # Signals for reporting progress to the progress bar
    progress = pyqtSignal(int)
    current_station = pyqtSignal(str)
    remaining_time_signal = pyqtSignal(int)

    def __init__(self, stat_dict, uuidict, timeseries):
        super(PoStationsFullTS, self).__init__()
        QObject.__init__(self)
        self.stat_dict = stat_dict
        self.uuidict = uuidict
        self.query = poBaseURL + "stations/"
        self.timeseries = timeseries
        self.keys.remove('water')
        self.keys_ts = ['ts'] 
        self.is_cancelled = False


    def extractTS(self, jsdata):
        """Extract a timeseries from json data and return pandas dataframe"""
        ls = []
        for elmnt in jsdata:
            ls.append([elmnt.get('timestamp',None), elmnt.get('value',None)])

        df = pd.DataFrame(ls,columns=['timestamp','value'])
        df['timestamp']=pd.to_datetime(df['timestamp'])
        return df

    def calculateROC(self, df, hours):
        """Calculate the rate of change in the last x hours of a timeseries"""
        if not df.empty:
            targettime = df.iloc[-1]['timestamp'] - pd.Timedelta(hours=hours)
            # find the closest row in the case that the target time does not correspond to an exact row
            prevval = df.iloc[(df['timestamp'] - targettime).abs().idxmin()]['value']
            roc = df.iloc[-1]['value'] - prevval
        else:
            roc = None
        return roc
        

    def convert2Feature(self, jsdata, stat, roc, unit):
        """Convert json data into a geojson feature"""
        feat = GjFeature()
        # set geometry
        try:
            feat.setCoordinates(self.uuidict[stat]['longitude'], self.uuidict[stat]['latitude'])
        except KeyError as e:
            print("Station can't be added: %s"%e)
            return None
        
        for k in self.keys:
            prop = {k : self.uuidict[stat].get(k,None)}
            feat.setProperty(prop)
        feat.setProperty({'Rate of Change' : roc})
        feat.setProperty({'unit':unit})
        feat.setProperty({'shortname':stat})
        return feat

    def loopThruStations(self, hours):
        """Make API calls for full timeseries of all stations, compute rate of change in last x hours, and append to a feature collection"""
        start_processing_time = QTime.currentTime()
        self.feature_collection = GjFeatureCollection()
        cnt = 0
        total_stations = len(self.stat_dict['stations'])
        for stat in list(self.stat_dict['stations'].keys()):
            if self.is_cancelled == True:
                return
            self.current_station.emit(stat)
            # Make API call for station stat
            apiurl = self.query + self.uuidict[stat]['uuid'] + '/' + self.timeseries + '/measurements.json'
            ur = Urlreader(apiurl)
            jsdata = ur.getJsonResponse()

            # Extract timeseries
            df = self.extractTS(jsdata)

            # Calculate ROC
            roc = self.calculateROC(df,hours)

            # Extract unit
            unit = self.stat_dict['stations'][stat]['unit']

            # Convert to feature
            feat = self.convert2Feature(jsdata, stat, roc, unit)

            # Add the feature to the collection object
            if feat:
                self.feature_collection.addFeature(feat)

            # Calculate % progress value and send to worker object
            cnt = cnt+1
            progress_value = int(100 * (cnt / total_stations))
            self.progress.emit(progress_value)

            # Estimating remaining time and send to worker object
            current_time = QTime.currentTime()
            elapsed_time = start_processing_time.secsTo(current_time)
            avg_time_per_station = elapsed_time / cnt
            remaining_stations = total_stations - cnt
            estimated_remaining_time = int(remaining_stations * avg_time_per_station)
            self.remaining_time_signal.emit(estimated_remaining_time)
            
            
