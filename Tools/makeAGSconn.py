'''
This script will publish SD files from a directory

==Inputs==
Connection type
Output location
Connection name
Server URL
Server Type
AdminUser
AdminPassword (sent in clear text)
Save user name
'''

import os
import arcpy


def makeAGSconnection(connectionType, outputLocation, connectionName, serverURL, serverType, userName, password, serverUserName):
    ''' Function to create an ArcGIS Server connection file using the arcpy.Mapping function "CreateGISServerConnectionFile"    
    '''
    
    outputAGS = os.path.join(outputLocation, connectionName + ".ags")
    
    if os.path.exists(outputAGS):
        arcpy.AddWarning("AGS connection file already exists and will be overwritten")
    
    
    try:   
        use_arcgis_desktop_staging_folder = True  #This setting not exposed in the tool UI
        arcpy.mapping.CreateGISServerConnectionFile(connectionType,
                                            outputLocation,
                                            connectionName,
                                            serverURL,
                                            serverType,
                                            use_arcgis_desktop_staging_folder,
                                            '',
                                            userName,
                                            password,
                                            serverUserName)
        arcpy.SetParameter(8, outputAGS)
        
    except:
        arcpy.AddError("Could not create AGS connection file")
        arcpy.GetMessages()

        
if __name__ == "__main__": 
    
    # Gather inputs    
    connectionType = arcpy.GetParameterAsText(0) 
    outputLocation = arcpy.GetParameterAsText(1)
    connectionName = arcpy.GetParameter(2) 
    serverURL = arcpy.GetParameter(3)
    serverType = arcpy.GetParameterAsText(4)
    userName = arcpy.GetParameterAsText(5)
    password = arcpy.GetParameterAsText(6)
    serverUserName = arcpy.GetParameterAsText(7)
    
    makeAGSconnection(connectionType, outputLocation, connectionName, serverURL, serverType, userName, password, serverUserName)