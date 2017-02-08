# Required imports
import urllib
import urllib2
import json


def gentoken(server, port, adminUser, adminPass, expiration=60):
    #Re-usable function to get a token required for Admin changes

    query_dict = {'username':   adminUser,
                  'password':   adminPass,
                  'expiration': str(expiration),
                  'client':     'requestip'}

    query_string = urllib.urlencode(query_dict)
    url = "http://{}:{}/arcgis/admin/generateToken".format(server, port)

    token = json.loads(urllib.urlopen(url + "?f=json", query_string).read())

    if "token" not in token:
        print (token['messages'])
        exit()
    else:
        # Return the token to the function which called for it
        return token['token']




def stopStartServices(server, port, adminUser, adminPass, stopStart, serviceList, token=None):
    ''' Function to stop, start or delete a service.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    stopStart = Stop|Start|Delete
    serviceList = List of services. A service must be in the <name>.<type> notation
    If a token exists, you can pass one in for use.
    '''

    # Get and set the token
    if token is None:
        token = gentoken(server, port, adminUser, adminPass)

    # modify the services(s)
    for service in serviceList:
        op_service_url = "http://{}:{}/arcgis/admin/services/{}/{}?token={}&f=json".format(server, port, service, stopStart, token)
        status = urllib2.urlopen(op_service_url, ' ').read()

        if 'success' in status:
            print (str(service) + " === " + str(stopStart))
        else:
            print (status)

    return



if __name__ == "__main__":

    # Gather inputs
    server = "gizmo"
    port = "6080"
    adminUser = "admin"
    adminPass = "admin"
    service = ["SampleWorldCities.MapServer"]    #Change this to the name of your mapservice (you need .MapServer at the end)


    # stop the service
    print ("stopping : {}".format(service))
    stopStartServices(server, port, adminUser, adminPass, "Stop", service)

    #
    # Optional code here to do something in your database... or a sleep or whatever
    #

    # start the service back up
    print ("starting : {}".format(service))
    stopStartServices(server, port, adminUser, adminPass, "Start", service)

    print ("done")





