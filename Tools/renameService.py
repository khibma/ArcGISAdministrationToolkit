'''
This script will rename an existing service

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
Existing Service (in <serviceName>.<serviceType> format)
New Service name (only string of new service name)
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


def renameService(server, port, adminUser, adminPass, service, newName, token=None):
    ''' Function to rename a service
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    service = String of existing service with type seperated by a period <serviceName>.<serviceType>
    newName = String of new service name
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)      
    
    service = urllib.quote(service.encode('utf8'))  
    
    # Check the service name for a folder:
    if "//" in service:
        serviceName = service.split('.')[0].split("//")[1]
        folderName = service.split('.')[0].split("//")[0] + "/" 
    else:
        serviceName = service.split('.')[0]
        folderName = ""
    
    renameService_dict = { "serviceName": serviceName,
                           "serviceType": service.split('.')[1],
                           "serviceNewName" : urllib.quote(newName.encode('utf8')) 
                         }
    
       
    rename_encode = urllib.urlencode(renameService_dict)     
    rename = "http://{}:{}/arcgis/admin/services/{}renameService?token={}&f=json".format(server, port, folderName, token)        
    status = urllib2.urlopen(rename, rename_encode ).read()
    
    
    if 'success' in status:
        arcpy.SetParameter(6, True)
    else:
        arcpy.SetParameter(6, False)
        arcpy.AddError(status)
    
        
if __name__ == "__main__":     
    
    # Gather inputs    
    server = arcpy.GetParameterAsText(0) 
    port = arcpy.GetParameterAsText(1) 
    adminUser = arcpy.GetParameterAsText(2) 
    adminPass = arcpy.GetParameterAsText(3) 
    service = arcpy.GetParameter(4) 
    newName = arcpy.GetParameterAsText(5)
    
    renameService(server, port, adminUser, adminPass, service, newName)
            
    