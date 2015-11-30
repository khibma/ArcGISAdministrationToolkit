'''
This script will create a new folder

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
Folder name
Folder description
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


def createFolder(server, port, adminUser, adminPass, folderName, folderDescription, token=None):
    ''' Function to create a folder
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    folderName = String with a folder name
    folderDescription = String with a description for the folder
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)    
        
    folderProp_dict = { "folderName": folderName,
                        "description": folderDescription                                            
                      }
    
    folder_encode = urllib.urlencode(folderProp_dict)            
    create = "http://{}:{}/arcgis/admin/services/createFolder?token={}&f=json".format(server, port, token)    
    status = urllib2.urlopen(create, folder_encode).read()

    
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
    folderName = arcpy.GetParameter(4) 
    folderDescription = arcpy.GetParameterAsText(5)
    
    createFolder(server, port, adminUser, adminPass, folderName, folderDescription)
            
    