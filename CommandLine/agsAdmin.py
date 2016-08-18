'''
NOTE! This code will only work when complied/executed against Python 2.7.x
It is NOT 3.x compatible.

This script makes use of the same functions found in the Code/AllFunctions.py samples.
It has been enhanced with more error trapping and uses command line arguments to run.
The script can be run as a python script:
C:\myScripts>c:\python27\python.exe agsAdmin.py myServer 6080 admin admin list

It has also been used to create a standalone executable (.exe) which you can use on a system without python.
Call the .exe in the same way you would call the python script (without the call to python.exe first)
C:\myScripts>agsAdmin.exe myServer 6080 admin admin list

If you make modifications to the script and want to re-build the .exe, install py2eye module, and execute it against the
setup.py file (included): C:\myScripts>c:\python27\python.exe setup.py py2exe

These scripts provided as samples and are not supported through Esri Technical Support.
Please direct questions to either the Python user forum : http://forums.arcgis.com/forums/117-Python
or the ArcGIS Server General : https://geonet.esri.com/community/developers/gis-developers/python

'''

# Required imports
import json
import sys
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


port = 6080
http = 'http'

def gentoken(server, portNum, adminUser, adminPass, expiration=60):
    # Re-usable function to get a token required for Admin changes


    sslURL = "http://{}:{}/arcgis/admin/generateToken?f=json".format(server, portNum)
    redirectURL = urlopen(sslURL).geturl()
    sslSettings = json.loads(urlopen(redirectURL).read())

    global port
    port = portNum
    try:
        if sslSettings['ssl']['supportsSSL']:
            port = sslSettings['ssl']['sslPort']
            global http
            http = 'https'
    except:
        pass

    query_dict = {'username':   adminUser,
                  'password':   adminPass,
                  'expiration': str(expiration),
                  'client':     'requestip',
                  'f':          'json'}

    query_string = encode(query_dict)
    url = "{}://{}:{}/arcgis/admin/generateToken".format(http, server, port)

    try:
        token = json.loads(urlopen(url, query_string).read())
        if "token" not in token or token == None:
            print ("Failed to get token, return message from server:")
            print (token)
            sys.exit()
        else:
            # Return the token to the function which called for it
            return token['token']

    except URLError as e:
        print ("Could not connect to machine {} on port {}".format(server, port))
        print (e)
        sys.exit()


def stopStartServices(server, portNum, adminUser, adminPass, stopStart, serviceList, token=None):
    ''' Function to stop, start or delete a service.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    stopStart = Stop|Start|Delete
    serviceList = List of services. A service must be in the <name>.<type> notation
    If a token exists, you can pass one in for use.
    '''

    # Get and set the token
    if token is None:
        token = gentoken(server, portNum, adminUser, adminPass)

    if serviceList == "all":
        serviceList = getServiceList(server, port, adminUser, adminPass, token)
        print(" \n")
    else:
        serviceList = [serviceList]


    # modify the services(s)
    for service in serviceList:
        op_service_url = "{}://{}:{}/arcgis/admin/services/{}/{}".format(http, server, port, service, stopStart)
        query = {'token':token,
                 'f':'json'}
        status = urlopen(op_service_url, data=encode(query)).read()

        if 'success' in status:
            print ("{} successfully performed on {}".format(stopStart, service))
        else:
            print ("Failed to perform operation. Returned message from the server:")
            print (status)

    return


def getServiceList(server, portNum, adminUser, adminPass, token=None):
    ''' Function to get all services
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.
    Note: Will not return any services in the Utilities or System folder
    '''

    if token is None:
        token = gentoken(server, portNum, adminUser, adminPass)

    services = []
    folder = ''
    URL = "{}://{}:{}/arcgis/admin/services{}?f=pjson&token={}".format(http, server, port, folder, token)

    try:
        serviceList = json.loads(urlopen(URL).read())
    except URLError as e:
        print (e)
        sys.exit()

    # Build up list of services at the root level
    for single in serviceList["services"]:
        services.append(single['serviceName'] + '.' + single['type'])

    # Build up list of folders and remove the System and Utilities folder (we dont want anyone playing with them)
    folderList = serviceList["folders"]
    folderList.remove("Utilities")
    folderList.remove("System")

    if len(folderList) > 0:
        for folder in folderList:
            URL = "{}://{}:{}/arcgis/admin/services/{}?f=pjson&token={}".format(http, server, port, folder, token)
            fList = json.loads(urlopen(URL).read())

            for single in fList["services"]:
                services.append(folder + "//" + single['serviceName'] + '.' + single['type'])

    if len(services) == 0:
        print ("No services found")
        return []
    else:
        print ("Services / State on {}:".format(server))
        for service in services:
            statusURL = "{}://{}:{}/arcgis/admin/services/{}/status?f=pjson&token={}".format(http, server, port, service, token)
            status = json.loads(urlopen(statusURL).read())
            print ("  {} >  {}".format(service, status["realTimeState"].title()))


    return services


if __name__ == "__main__":

    args = sys.argv

    if len(args) == 1:
        print ("Use switch '/?' for help")

    else:

        if args[1] == '/?':
            print ("agsAdmin.exe utility provides a way to script ArcGIS Server administrative tasks. \n\
            This module is built on python and compiled into an exe which you can call from command\n\
            line or a batch file. Note that all admin usernames and passwords are sent in clear text.")

            print ("Usage: \n\
            List services: agsAdmin.exe server port adminUser adminPass list \n\
            Stop a service: agsAdmin.exe server port adminUser adminPass stop Map.MapService \n\
            Start a service: agsAdmin.exe server port adminUser adminPass start Buffer.GPServer \n\
            Delete a service: agsAdmin.exe server port adminUser adminPass delete Find.GeocodeServer \n\
            The 'all' keyword can be used in place of a service name to stop, start or delete all services \n\
            \n\
            eg: agsAdmin.exe myServer 6080 admin p@$$w0rd list\n\
            eg: agsAdmin.exe myServer 6080 admin p@$$w0rd start ForestCover.MapService\n\
            eg. agsAdmin.exe myServer 6080 admin p@$$w0rd stop all \n\
            ")
        else:
            if len(args) < 6:
                print ("Not enough arguments")
            else:
                if args[5].lower() == "list":
                    getServiceList(*args[1:5])
                elif args[5].lower() in ['start', 'stop', 'delete']:
                    stopStartServices(*args[1:7])
                else:
                    print ("Unknown command:  {}".format(str(args[5])))
