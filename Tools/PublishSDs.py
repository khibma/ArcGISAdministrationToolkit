'''
This script will publish SD files from a directory

==Inputs==
AGS Connection file
Directory of SDs (not required when used in scripting)
SD File as a list
Immediately start service (boolean)
REST URL to query the server for existing folders (not required when used in scripting)
Folder name
'''

import arcpy


def publishSDs(agsConnectionFile, SDList, started, folder):  
    '''Function to publish SDs. Takes an AGS connection file and a list of SDs.
    If you only have 1 SD, you can send it in a list ['c:\foo\mySd.sd']        
    '''  
    
    if folder != "":  
        folderType = 'EXISTING'        
    else:
        folderType = "FROM_SERVICE_DEFINITION"
        folder = ""
    
    if started == True:
        startUp = "STARTED"
    else:
        startUp = "STOPPED"        
    
    for sd in SDList:       
        try:
            arcpy.UploadServiceDefinition_server(sd, agsConnectionFile, '', '', 
                                                 in_folder_type=folderType,
                                                 in_folder=folder,
                                                 in_startupType=startUp)
            
            arcpy.AddMessage("Published :  " + str(sd[:-3]))
        except:            
            arcpy.AddWarning("FAILED to publish " + str(sd[:-3]))
            arcpy.GetMessages(2)
            
    
    return 


if __name__ == "__main__": 
    
    # Gather inputs    
    agsConnectionFile = arcpy.GetParameterAsText(0)
    SDList = arcpy.GetParameter(2)
    started = arcpy.GetParameter(3)
    folder = arcpy.GetParameterAsText(5)
    
    publishSDs(agsConnectionFile, SDList, started, folder)