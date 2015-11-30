#This script not used by any tools directly
'''
This script will return all folders on a server in a list.
NOTE: This uses the Services Directory, not the REST Admin

==Inputs==
ServerName
Port
'''

import urllib2, json
import arcpy


def getFolders(server, port):
    ''' Function to get all folders on a server   
    '''        
    
    foldersURL = "http://{}:{}/arcgis/rest/services/?f=pjson".format(server, port)    
    status = json.loads(urllib2.urlopen(folders, '').read())
        
    folders = status["folders"]
    
    return folders
    
        
if __name__ == "__main__":     
    
    # Gather inputs    
    server = arcpy.GetParameterAsText(0)
    port = arcpy.GetParameterAsText(1)
        
    getFolders(server, port)
