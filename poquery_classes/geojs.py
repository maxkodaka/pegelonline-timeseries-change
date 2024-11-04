import json

class GjFeatureCollection:

    def __init__(self):
        self._dict = {
            "type": "FeatureCollection",
            "features": []
        }

    def getDict(self):
        return self._dict

    def addFeature(self, feature):
        d = feature.getDict()
        self._dict['features'].append(d)

    def write(self, path):
        with open(path, 'w') as outfile:
            json.dump(self._dict, outfile)


class GjFeature:

    def __init__(self):
        self._dict = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": []
            },
            "properties": {}
        }

    def getDict(self):
        return self._dict

    def setCoordinates(self, lon, lat):
        # add lon, lat to the internal data "_dict"
        self._dict['geometry']['coordinates'] = [lon, lat]

    def setProperty(self, prop_dict):
        # add 'prop_dict' to the internal data "_dict"
        self._dict['properties'].update(prop_dict)