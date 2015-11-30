'''
This script will stop or start all selected services

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
Stop or Start 
Service(s) (multivalue list)
'''

import urllib, urllib2, json
import arcpy


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
        arcpy.AddError(token['messages'])
        quit()
    else:
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
    
    # Getting services from tool validation creates a semicolon delimited list that needs to be broken up
    services = serviceList.split(';')
    
    #modify the services(s)    
    for service in services:        
        service = urllib.quote(service.encode('utf8'))
        op_service_url = "http://{}:{}/arcgis/admin/services/{}/{}?token={}&f=json".format(server, port, service, stopStart, token)        
        status = urllib2.urlopen(op_service_url, ' ').read()
        
        if 'success' in status:
            arcpy.AddMessage(str(service) + " === " + str(stopStart))
        else:
            arcpy.AddWarning(status)
    
    return 


if __name__ == "__main__": 
    
    # Gather inputs    
    server = arcpy.GetParameterAsText(0) 
    port = arcpy.GetParameterAsText(1) 
    adminUser = arcpy.GetParameterAsText(2) 
    adminPass = arcpy.GetParameterAsText(3) 
    stopStart = arcpy.GetParameter(4) 
    serviceList = arcpy.GetParameterAsText(5) 
    
    stopStartServices(server, port, adminUser, adminPass, stopStart, serviceList)