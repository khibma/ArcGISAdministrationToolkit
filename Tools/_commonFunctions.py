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


class connectionHelper(object):

    def __init__(self, server, port, username, password):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.token = None
        self.token = self.gentoken(server, port, username, password)
        self.SSL = self.checkSSL()
        self.prefix = 'https' if self.SSL else 'http'
        if self.prefix == 'https': self.port= 6443
        self.baseURL = "{pre}://{server}:{port}/arcgis/admin".format(pre=self.prefix, server=self.server, port=self.port)


    def gentoken(self, server, port, adminUser, adminPass, expiration=60):
        #Re-usable function to get a token required for Admin changes

        query_dict = {'username':   adminUser,
                      'password':   adminPass,
                      'expiration': str(expiration),
                      'client':     'requestip',
                      'f':           'json'}

        url = "http://{}:{}/arcgis/admin/generateToken".format(server, port)

        token = self.url_request(url, query_dict, "POST")

        if "token" not in token:
            print (token['messages'])
            exit()
        else:
            # Return the token to the function which called for it
            return token['token']


    def checkSSL(self):

        sslURL = "http://{}:{}/arcgis/admin/security/config?f=pjson".format(self.server, self.port)
        params = {'token': self.token,
                  'f': 'json'}
        sslSettings = self.url_request(sslURL, params, 'POST')
        try:
            return sslSettings['sslEnabled']
        except:
            print("Error getting SSL setting, assuming HTTPS is disabled")
            return False


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


    def getServiceList(self, folder=''):
        ''' Function to get all services
        Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
        If a token exists, you can pass one in for use.
        Note: Will not return any services in the Utilities or System folder    '''


        if self.token is None:
            self.token = self.gentoken()

        services = []
        URL = "{}://{}:{}/arcgis/admin/services{}?f=pjson&token={}".format(self.http, self.server, self.port, folder, self.token)

        serviceList = json.loads(urllib2.urlopen(URL).read())

        # Build up list of services at the root level
        for single in serviceList["services"]:
            services.append(single['serviceName'] + '.' + single['type'])

        # Build up list of folders and remove the System and Utilities folder (we dont want anyone playing with them)
        folderList = serviceList["folders"]
        folderList.remove("Utilities")
        folderList.remove("System")

        if len(folderList) > 0:
            for folder in folderList:
                URL = "{}://{}:{}/arcgis/admin/services/{}?f=pjson&token={}".format(self.http, self.server, self.port, folder, self.token)
                fList = json.loads(urllib2.urlopen(URL).read())

                for single in fList["services"]:
                    services.append(folder + "//" + single['serviceName'] + '.' + single['type'])

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