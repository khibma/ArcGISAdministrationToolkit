'''
This script will upload and register an SOE

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
SOE (file)
'''

import json, urllib, urllib2
import arcpy
import requests


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
    

def upload(server, port, adminUser, adminPass, fileinput, token=None):
    ''' Function to upload a file to the REST Admin
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    fileinput = path to file to upload. (file upload will be done in binary)
    NOTE: Dependency on 3rd party module "requests" for file upload 
        > http://docs.python-requests.org/en/latest/index.html
    If a token exists, you can pass one in for use.  
    '''  
    
    # Get and set the token
    if token is None:  
        token = gentoken(server, port, adminUser, adminPass)     
  
    # Properties used to upload a file using the request module
    files = {"itemFile": open(fileinput, 'rb')}
    files["f"] = "json"        
    
    URL='http://{}:{}/arcgis/admin/uploads/upload'.format(server, port)
    response = requests.post(URL+"?token="+token, files=files);
         
    json_response = json.loads(response.text)
    
    if "item" in json_response:                
        itemID = json_response["item"]["itemID"]             
        registerSOE(server, port, adminUser, adminPass, itemID)        
    else:
        print json_response
        
    return    
                
        
def registerSOE(server, port, adminUser, adminPass, itemID, token=None):
    ''' Function to upload a file to the REST Admin
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    itemID = itemID of an uploaded SOE the server will register.    
    If a token exists, you can pass one in for use.      '''
    
    # Get and set the token
    if token is None:  
        token = gentoken(server,  port, "admin", "admin")     
    
    # Registration of an SOE only requires an itemID. The single item dictionary is encoded in place
    SOE_encode = urllib.urlencode({"id":itemID})   
    
    register = "http://{}:{}/arcgis/admin/services/types/extensions/register?token={}&f=json".format(server, port, token)    
    status = urllib2.urlopen(register, SOE_encode).read()
    
    if 'success' in status:
        arcpy.AddMessage("Succesfully registed SOE")
    else:
        arcpy.AddError("Could not register SOE")
        arcpy.AddMessage(status)
    
    return      
    
                
if __name__ == "__main__": 
    
    # Gather inputs    
    server = arcpy.GetParameterAsText(0) 
    port = arcpy.GetParameterAsText(1) 
    adminUser = arcpy.GetParameterAsText(2)    
    adminPass = arcpy.GetParameterAsText(3)
    fileinput = arcpy.GetParameterAsText(4) 
        
    upload(server, port, adminUser, adminPass, fileinput)