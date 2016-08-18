'''
This script provides functions used to administer ArcGIS Server 10.1+.
Most functions below make calls to the REST Admin, using specific URLS to perform an action.
The functions below DO NOT make use of arcpy, as such they can be run on any machine with Python 2.7.x or 3.4.x installed
This list is not intended to be a complete list of functions to work with ArcGIS Server. It does provide the most common
actions and templates to extend or a place to start your own.
See the REST Admin API for comprehensive commands and explanation.
Examples on how the functions are called can be found at the bottom of this file.

Date : June 15, 2012
Updated: August, 2016

Author:        Kevin - khibma@esri.com
Contributors:  various Esri staff

These scripts provided as samples and are not supported through Esri Technical Support.
Please direct questions to either the Python user forum : https://geonet.esri.com/community/developers/gis-developers/python
or the ArcGIS Server General : https://geonet.esri.com/community/gis/enterprise-gis/arcgis-for-server

See the ArcGIS Server help for interactive scripts and further examples on using the REST Admin API through Python:
http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#/The_ArcGIS_REST_API/02r300000054000000/
'''

# Required imports
import json
import datetime
from io import BytesIO
import gzip
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


class ConnHandler(object):

    def __init__(self, server, port, username, password):
        self.token = None
        self.server = server
        self.port = port
        self.SSL = self.checkSSL()
        self.prefix = 'https' if self.SSL else 'http'
        self.username = username
        self.password = password

        self.baseURL = "{pre}://{server}:{port}/arcgis/admin".format(pre=self.prefix, server=self.server, port=self.port)
        self.token = self.gentoken(username, password)

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


    def url_request(self, in_url, params=None, req_type="GET"):

        if params == None:
            params = {'f':'json'}
        elif 'f' not in params:
            params['f'] = 'json'
        if "token" not in params and self.token:
            params['token'] = self.token

        if req_type == 'GET':
            req = request('?'.join((in_url, encode(params))))
        else:
            req = request(
                in_url, encode(params).encode('UTF-8'))

        req.add_header('Accept-encoding', 'gzip')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        req.add_header('User-Agent', 'AllFunctions.py')

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


    """ Begin functions to work with the server """

    def modifyLogs(self, clearLogs=False, logLevel="WARNING"):
        ''' Function to clear logs and modify log settings.
        Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
        clearLogs = True|False
        logLevel = SEVERE|WARNING|FINE|VERBOSE|DEBUG
        '''

        # Clear existing logs
        if clearLogs:
            clearLogs_url = "{}/logs/clean".format(self.baseURL)
            status = self.url_request(clearLogs_url, req_type='POST')

            if 'success' in status.values():
                print ("Cleared log files")

        # Get the current logDir, maxErrorReportsCount and maxLogFileAge as we dont want to modify those
        currLogSettings_url = "{}/logs/settings".format(self.baseURL)
        logSettingProps = self.url_request(currLogSettings_url, req_type='GET')['settings']

        # Place the current settings, along with new log setting back into the payload
        logLevel_dict = {"logDir": logSettingProps['logDir'],
                         "logLevel": logLevel,
                         "maxErrorReportsCount": logSettingProps['maxErrorReportsCount'],
                         "maxLogFileAge": logSettingProps['maxLogFileAge']
                        }

        # Modify the logLevel
        logLevel_url = "{}/logs/settings/edit".format(self.baseURL)
        logStatus = self.url_request(logLevel_url, logLevel_dict, 'POST')


        if logStatus['status'] == 'success':
            print ("Succesfully changed log level to {}".format(logLevel))
        else:
            print ("Log level not changed")

        return


    def createFolder(self, folderName, folderDescription):
        ''' Function to create a folder
        Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
        folderName = String with a folder name
        folderDescription = String with a description for the folder
        '''

        # Dictionary of properties to create a folder
        folderProp_dict = { "folderName": folderName,
                            "description": folderDescription
                          }

        create_url = "{}/services/createFolder".format(self.baseURL)
        status = self.url_request(create_url, folderProp_dict, 'POST')


        if 'success' in status.values():
            print ("Created folder: {}".format(folderName))
        else:
            print ("Could not create folder")
            print (" >> {}".format(status))

        return


    def getFolders(self):
        ''' Function to get all folders on a server
        Note: Uses the Services Directory, not the REST Admin
        '''

        folders_url = "{}/services/?f=pjson".format(self.baseURL)
        status = self.url_request(folders_url, req_type='POST')

        folders = status["folders"]

        # Return a list of folders to the function which called for them
        return folders


    def renameService(self, service, newName):
        ''' Function to rename a service
        Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
        service = String of existing service with type separated by a period <serviceName>.<serviceType>
        newName = String of new service name

        '''

        service = parse.quote(service.encode('utf8'))

        # Check the service name for a folder:
        if "//" in service:
            serviceName = service.split('.')[0].split("//")[1]
            folderName = service.split('.')[0].split("//")[0] + "/"
        else:
            serviceName = service.split('.')[0]
            folderName = ""

        renameService_dict = { "serviceName": serviceName,
                               "serviceType": service.split('.')[1],
                               "serviceNewName" : parse.quote(newName.encode('utf8'))
                             }

        rename_url = "{}/services/renameService".format(self.baseURL)
        status = self.url_request(rename_url, renameService_dict, 'POST')


        if 'success' in status.values():
            print ("Succesfully renamed service to : {}".format(newName))
        else:
            print ("Could not rename service")
            print (status)

        return

    def stopStartServices(self, stopStart, serviceList):
        ''' Function to stop, start or delete a service.
        Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
        stopStart = Stop|Start|Delete
        serviceList = List of services. A service must be in the <name>.<type> notation
        '''
        if type(serviceList) == str:
            print("Service list must be of type:list")
            return

        # modify the services(s)
        for service in serviceList:
            op_service_url = "{}/services/{}/{}".format(self.baseURL, service, stopStart)
            status = self.url_request(op_service_url, req_type='POST')

            if 'success' in status.values():
                print (str(service) + " === " + str(stopStart))
            else:
                print (status)

        return


    def upload(self, fileinput):
        ''' Function to upload a file to the REST Admin
        Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
        fileinput = path to file to upload. (file upload will be done in binary)
        NOTE: Dependency on 3rd party module "requests" for file upload
            > http://docs.python-requests.org/en/latest/index.html
        '''

        # 3rd party module dependency
        import requests

        # Properties used to upload a file using the request module
        files = {"itemFile": open(fileinput, 'rb')}
        files["f"] = "json"

        URL='{}/uploads/upload'.format(self.baseURL)
        response = requests.post(URL+"?token="+self.token, files=files);

        json_response = json.loads(response.text)

        if "item" in json_response:
            itemID = json_response["item"]["itemID"]
            #Note : this function calls the registerSOE function. Remove next line if unnecessary
            self.registerSOE(itemID)
        else:
            print (json_response)

        return


    def registerSOE(self, itemID):
        ''' Function to upload a file to the REST Admin
        Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
        itemID = itemID of an uploaded SOE the server will register.
        '''

        # Registration of an SOE only requires an itemID. The single item dictionary is encoded in place
        #SOE_encode = encode({"id":itemID})

        register_url = "{}/services/types/extensions/register".format(self.baseURL)
        status = self.url_request(register_url, {"id":itemID})

        if 'success' in status.values():
            print ("Succesfully registed SOE")
        else:
            print ("Could not register SOE")
            print (status)

        return


    def getServiceList(self, folderList=""):
        ''' Function to get all services
            Note: Will not return any services in the Utilities or System folder
        '''

        services = []
        service_url = "{}/services".format(self.baseURL)

        serviceList = self.url_request(service_url)

        # Build up list of services at the root level
        for single in serviceList["services"]:
            services.append(single['serviceName'] + '.' + single['type'])

        # Build up list of folders and remove the System and Utilities folder (we dont want anyone playing with them)
        folderList = serviceList["folders"]
        folderList.remove("Utilities")
        folderList.remove("System")

        if len(folderList) > 0:
            for folder in folderList:
                URL = "{}/services/{}".format(self.baseURL, folder)
                fList = self.url_request(URL)

                for single in fList["services"]:
                    services.append(folder + "//" + single['serviceName'] + '.' + single['type'])

        #print (services)
        return services


    def getServerInfo(self):
        ''' Function to get and display a detailed report about a server
        Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
        service = String of existing service with type seperated by a period <serviceName>.<serviceType>
        '''

        report = "*-----------------------------------------------*\n\n"

        # Get Cluster and Machine info
        cluster_url = "{}/clusters".format(self.baseURL)
        jCluster = self.url_request(cluster_url)

        if len(jCluster["clusters"]) == 0:
            report += "No clusters found\n\n"
        else:
            for cluster in jCluster["clusters"]:
                report += "Cluster: {} is {}\n".format(cluster["clusterName"], cluster["configuredState"])
                if len(cluster["machineNames"])     == 0:
                    report += "    No machines associated with cluster\n"
                else:
                    # Get individual Machine info
                    for machine in cluster["machineNames"]:
                        machine_url = "{}/machines/{}".format(self.baseURL, machine)
                        jMachine = self.url_request(machine_url)
                        report += "    Machine: {} is {}. (Platform: {})\n".format(machine, jMachine["configuredState"],jMachine["platform"])


        # Get Version and Build
        info_url = "{}/info".format(self.baseURL)
        jInfo = self.url_request(info_url)
        report += "\nVersion: {}\nBuild:   {}\n\n".format(jInfo ["currentversion"], jInfo ["currentbuild"])


        # Get Log level
        log_url = "{}/logs/settings".format(self.baseURL)
        jLog = self.url_request(log_url)
        report += "Log level: {}\n\n".format(jLog["settings"]["logLevel"])


        #Get License information
        license_url = "{}/system/licenses".format(self.baseURL)
        jLicense = self.url_request(license_url)
        report += "License is: {} / {}\n".format(jLicense["edition"]["name"], jLicense["level"]["name"])
        if jLicense["edition"]["canExpire"] == True:
            d = datetime.date.fromtimestamp(jLicense["edition"]["expiration"] // 1000) #time in milliseconds since epoch
            report += "License set to expire: {}\n".format(datetime.datetime.strftime(d, '%Y-%m-%d'))
        else:
            report += "License does not expire\n"


        if len(jLicense["extensions"]) == 0:
            report += "No available extensions\n"
        else:
            report += "Available Extenstions........\n"
            for name in jLicense["extensions"]:
                report += "extension:  {}\n".format(name["name"])


        report += "\n*-----------------------------------------------*\n"

        print (report)



##### EXAMPLE CALLS TO ABOVE FUNCTIONS #####
server = "arcola"
port = 6080
admin = "admin"
apass = "admin"
myAGS = ConnHandler(server, port, admin, apass)

# Register an SOE:
#upload("prodSrv", 6080, "admin", "admin", r"c:\development\SOES\querySOE.soe")

# Stop 3 services from a list:
#serviceList = ["CitizenMapping.MapServer","CitizenInput.GPServer","basemap.MapServer"]
#myAGS.stopStartServices("Stop", serviceList)

# Get all services on a server and start them all:
serviceList = myAGS.getServiceList()
print(serviceList)
#myAGS.stopStartServices("Start", serviceList)

# Clear log files and change to Debug:
myAGS.modifyLogs(True, "DEBUG")

# Create a folder:
myAGS.createFolder("testServices", "Folder for test services")

# Get a list of folders and assign to a variable:
serverFolders = myAGS.getFolders()
print (serverFolders)

# Print out information about a server
myAGS.getServerInfo()