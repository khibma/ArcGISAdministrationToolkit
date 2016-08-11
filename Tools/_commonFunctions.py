import json
import datetime
from io import BytesIO
import gzip
import sys
import codecs
import uuid
import mimetypes

try:
    import urllib.parse as parse
    from urllib.request import urlopen as urlopen
    from urllib.request import Request as request
    from urllib.request import HTTPError, URLError
    from urllib.parse import urlencode as encode
# py2
except ImportError:
    from urllib2 import urlparse as parse
    from urllib2 import urlopen as urlopen
    from urllib2 import Request as request
    from urllib2 import HTTPError, URLError
    from urllib import urlencode as encode
    unicode = str

import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context


class connectionHelper(object):

    def __init__(self, server, port, username, password):
        self.token = None
        self.server = server
        self.port = port
        self.SSL = self.checkSSL()
        self.prefix = 'https' if self.SSL else 'http'
        self.username = username
        self.password = password

        self.baseURL = "{pre}://{server}:{port}/arcgis/admin".format(pre=self.prefix, server=self.server, port=self.port)
        self.token = self.gentoken(server, port, username, password)

    def checkSSL(self):

        sslURL = "http://{}:{}/arcgis/admin/generateToken?f=json".format(self.server, self.port)
        sslSettings = self.url_request(sslURL, {'f': 'json'}, 'POST')
        try:
            if sslSettings['ssl']['supportsSSL']:
                self.port = sslSettings['ssl']['sslPort']
                return True
            else:
                return False
        except:
            print("Error getting SSL setting, using HTTP")
            return False

    def gentoken(self, adminUser, adminPass, expiration=60):
        # Not to be called directly. The object will handle getting and setting the token

        query_dict = {'username':   adminUser,
                      'password':   adminPass,
                      'expiration': str(expiration),
                      'client':     'requestip',
                      'f':           'json'}

        url = "{}/generateToken".format(self.baseURL, self.port)

        token = self.url_request(url, query_dict, "POST")

        if not token or "token" not in token:
            print ("no token: {}".format(token))
        else:
            return token['token']


    def url_request(self, in_url, params=None, req_type="GET", headers=None):

        if params == None:
            params = {'f':'json'}
        elif 'f' not in params:
            params['f'] = 'json'
        if "token" not in params and self.token:
            params['token'] = self.token

        if req_type == 'GET':
            req = request('?'.join((in_url, encode(params))))
        elif req_type == 'MULTIPART':
            req = request(in_url, params)
        else:
            req = request(
                in_url, encode(params).encode('UTF-8'))

        req.add_header('Accept-encoding', 'gzip')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        req.add_header('User-Agent', 'AllFunctions.py')
        if headers:
            for key, value in list(headers.items()):
                req.add_header(key, value)

        try:
            response = urlopen(req)
        except HTTPError as e:
            print("HTTP_ERROR_MSG {} -- {}".format(in_url, e.code))
            return
        except URLError as e:
            print("URL_ERROR_MSG {} -- {}".format(in_url, e.reason))
            return

        if response.info().get('Content-Encoding') == 'gzip':
            buf = BytesIO(response.read())
            with gzip.GzipFile(fileobj=buf) as gzip_file:
                response_bytes = gzip_file.read()
        else:
            response_bytes = response.read()

        response_text = response_bytes.decode('UTF-8')

        return json.loads(response_text)


    def getServiceList(self, folderList=''):
        ''' Function to get all services
        Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
        Note: Will not return any services in the Utilities or System folder
        '''

        services = []
        service_url = "{}/services".format(self.baseURL)

        serviceList = self.url_request(service_url)

        # Build up list of services at the root level
        for single in serviceList["services"]:
            statusURL = "{}/services/{}/status".format(self.baseURL, single['serviceName'] + '.' + single['type'])
            serviceStatus = self.url_request(statusURL, req_type="GET")
            services.append("{}--[{}]".format(single['serviceName'] + '.' + single['type'],
                                             serviceStatus['realTimeState']))

        # Build up list of folders and remove the System and Utilities folder (we dont want anyone playing with them)
        folderList = serviceList["folders"]
        folderList.remove("Utilities")
        folderList.remove("System")

        if len(folderList) > 0:
            for folder in folderList:
                URL = "{}/services/{}".format(self.baseURL, folder)
                fList = self.url_request(URL)

                for single in fList["services"]:
                    statusURL = "{}/services/{}/{}/status".format(self.baseURL, folder,
                                                                  single['serviceName'] + '.' + single['type'])
                    serviceStatus = self.url_request(statusURL, req_type="GET")
                    services.append("{}/{}--[{}]".format(folder, single['serviceName'] + '.' + single['type'],
                                                        serviceStatus['realTimeState']))

        return services



class MultipartFormdataEncoder(object):
    """
    Usage:   request_headers, request_data =
                 MultipartFormdataEncoder().encodeForm(params, files)
    Inputs:
       params = {"f": "json", "token": token, "type": item_type,
                 "title": title, "tags": tags, "description": description}
       files = {"file": {"filename": "some_file.sd", "content": content}}
           Note:  content = open(file_path, "rb").read()
    """

    def __init__(self):
        self.boundary = uuid.uuid4().hex
        self.content_type = {
            "Content-Type": "multipart/form-data; boundary={}".format(self.boundary)
        }

    @classmethod
    def u(cls, s):
        if sys.hexversion < 0x03000000 and isinstance(s, str):
            s = s.decode('utf-8')
        if sys.hexversion >= 0x03000000 and isinstance(s, bytes):
            s = s.decode('utf-8')
        return s

    def iter(self, fields, files):
        """
        Yield bytes for body. See class description for usage.
        """

        encoder = codecs.getencoder('utf-8')
        for key, value in fields.items():
            yield encoder('--{}\r\n'.format(self.boundary))
            yield encoder(
                self.u('Content-Disposition: form-data; name="{}"\r\n').format(key))
            yield encoder('\r\n')
            if isinstance(value, int) or isinstance(value, float):
                value = str(value)
            yield encoder(self.u(value))
            yield encoder('\r\n')

        for key, value in files.items():
            if "filename" in value:
                filename = value.get("filename")
                content_disp = 'Content-Disposition: form-data;name=' + \
                               '"{}"; filename="{}"\r\n'.format(key, filename)
                content_type = 'Content-Type: {}\r\n'.format(
                    mimetypes.guess_type(filename)[0] or 'application/octet-stream')
                yield encoder('--{}\r\n'.format(self.boundary))
                yield encoder(content_disp)
                yield encoder(content_type)
            yield encoder('\r\n')
            if "content" in value:
                buff = value.get("content")
                yield (buff, len(buff))
            yield encoder('\r\n')

        yield encoder('--{}--\r\n'.format(self.boundary))

    def encodeForm(self, fields, files):
        body = BytesIO()
        for chunk, chunk_len in self.iter(fields, files):
            body.write(chunk)
        self.content_type["Content-Length"] = str(len(body.getvalue()))
        return self.content_type, body.getvalue()

b = connectionHelper("arcola", 6080, "admin", "admin")
