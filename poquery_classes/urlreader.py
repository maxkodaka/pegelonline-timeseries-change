# urlreader, version 3
# 05.05.2023
import os
import json
import gzip

from urllib import request
## just to have it
from urllib.parse import quote, unquote, urlparse
import urllib.error

class Urlreader(object):

    def __init__(self, url):

        self.url = url
        self.code = None
        self.headers = {}

    def openURL(self):
        """Send a request to url, return the response"""
        try:
            rq = request.Request(self.url)
            ## added gzip comp to request header
            rq.add_header('Accept-Encoding', 'gzip')
            response = request.urlopen(rq)
            self.code = response.code
            ## for gzip comp: store response header
            self.headers = dict(response.headers)
            return response

        except urllib.error.HTTPError as e:
            print ("HTTP error reading url:", self.url)
            print ("Code", e.code, e.msg)
            self.code = e.code
            #print ("Returns", e.read())

        except urllib.error.URLError as e:
            print ("URL error reading url:", self.url)
            print ("Reason:", e.reason)

        return None


    def getDataResponse(self):
        """download into data buffer/byte string b''"""

        # default return value
        data = b""
        response = self.openURL()

        if response:
            # check if headers has 'Content-Encoding' == 'gzip'
            if response.headers['Content-Encoding'] == 'gzip':
                data = gzip.GzipFile(fileobj=response).read()
            else:
                data = response.read()

        return data

    def getJsonResponse(self):
        """load a json structure from a REST-URL, returns a list/dict python object"""

        data = self.getDataResponse()

        if data:
            jsdata = json.loads(data)
            return jsdata
        else:
            return {}

    def getFileResponse(self, dest):
        """read response from url, save it to dest/filename.
        filename will be extracted from the URL."""

        data = self.getDataResponse()
        if not data or data == b'':
            return ""

        ## filename extraction from url
        result = urllib.parse.urlparse(self.url)
        ## path may be not present or just '/'
        fn = os.path.basename(result.path if len(result.path) > 1 else result.hostname)
        file_name = os.path.join(dest, fn)

        # save to file
        with open(file_name, 'wb') as savefile:
            savefile.write(data)

        # return file_name
        return file_name

if __name__ == '__main__':

    # data-response: html
    url = 'https://www.python.org/'
    ur = Urlreader(url)
    result = ur.getDataResponse()
    print("%s, code: %s, data: %s"%(url, ur.code, result[:1024]))

    # data-response: error
    url = 'https://www.python.org/fish.html'
    ur = Urlreader(url)
    result = ur.getDataResponse()
    print("%s, code: %s, data: %s"%(url, ur.code, result))

    # file-reponse: image
    url = "https://www.pegelonline.wsv.de/img/wsv_rgb_m.jpg"
    ur = Urlreader(url)
    result = ur.getFileResponse('c:/temp')
    print(url, result)

    # json-response
    url = "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json"
    ur = Urlreader(url)
    result = ur.getJsonResponse()
    print(ur.code, type(result), len(result))

    # save file: URL has no path for filename
    url = 'https://www.python.org/'
    ur = Urlreader(url)
    result = ur.getFileResponse('c:/temp')
    print("%s data: %s"%(url, result))

    # save file: URL with path and query
    url = "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json?waters=RHEIN,MAIN"
    ur = Urlreader(url)
    result = ur.getFileResponse('C:/temp')
    print(ur.code, type(result), result)
