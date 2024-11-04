from minimal_graph.poquery_classes import poBaseURL
from minimal_graph.poquery_classes.geojs import GjFeature, GjFeatureCollection
from minimal_graph.poquery_classes.poqueries import PoQuery, PoStations, PoStationsTS, PoStationsCM

def main():
    print(poBaseURL)
    #pobase = PoQuery(r"D:\Lehre\gap2\s3\stations.json")
    postat = PoStationsTS()
    #gjfeat = GjFeature()
    #gjcoll = GjFeatureCollection()
    return postat

if __name__ == '__main__':
    stations = main()
    print(stations)
    stations.read()
    #stations.write("c:/temp/foo-cw.geojson")
    simple_dict = stations.getTimeseriesSimple()

    stats = PoStationsCM("Q")
    stats.read()