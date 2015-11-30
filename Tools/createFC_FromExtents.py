#This script not used by any tools directly
'''
This script will create a FC from extents within the logs.
Relies heavily on the code and concepts from the help topic: Example: Write requested map extents to a feature class
http://resources.arcgis.com/en/help/main/10.1/#/Example_Write_requested_map_extents_to_a_feature_class/0154000005w8000000/

==Inputs==
ServerName
Port
AdminUser
AdminPassword (sent in clear text)
'''

import urllib, urllib2, json
import os, datetime
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

  
    
def makeFC_FromExtents(server, port, adminUser, adminPass, mapService, outputFC, token=None):
    ''' Function to get all services
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    Note: Will not return any services in the Utilities or System folder
    '''    
        
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)   
    
    #mapService = mapService.replace( ".", "/")
    mapService = urllib.quote(mapService.encode('utf8'))    
       
    extentURL = "http://{}:{}/arcgis/rest/services/{}".format( server, port, mapService.replace( ".", "/"))    
    fullExtent = getFullExtent(extentURL)        
    
    
    logQueryURL = "http://{}:{}/arcgis/admin/logs/query".format(server, port)        
    logFilter = "{'services': ['" + mapService + "']}"        
    params = urllib.urlencode({'level': 'FINE', 'filter': logFilter, 'token': token, 'f': 'json'})   
    extentData = urllib2.urlopen(logQueryURL, params).read()
    
    print logQueryURL
    
    if 'success' not in extentData:        
        arcpy.AddError("Error while querying logs: " + str(extentData))      
        return
    
    else:
        # Got good data, proceed....      
        dataObj = json.loads(extentData)
                
        # Create a featureclass, and open a cursor
        fc = createFC( outputFC, fullExtent[ "spatialReference"][ "wkid"])
        cursorFC = arcpy.da.InsertCursor(fc, ["SHAPE@", "EventDate", "Scale", "InvScale", "Width", "Height"])
          
        # Need this variable to track number of events found for ExportMapImage call
        logEvents = 0
        
        # Need Array to hold Shape
        shapeArray = arcpy.Array()
        
        # Iterate over messages
        for item in dataObj[ "logMessages"]:
            eventDateTime = datetime.datetime.fromtimestamp( float( item[ "time"]) / 1000)
            
            if item[ "message"].startswith( "Extent:"):
                eventScale = None     # Scale
                eventInvScale = None  # Inverse-Scale
                eventWidth = None     # Width
                eventHeight = None    # Height
                
                # Cycle through message details
                for pair in item[ "message"].replace(" ", "").split( ";"):
                    if pair.count( ":") == 1:
                        key, val = pair.split( ":")
                        
                        # Pick out Extent
                        if key == "Extent" and val.count( ",") == 3:
                            # Split into ordinate values
                            MinX, MinY, MaxX, MaxY = val.split( ",")
                            MinX = float( MinX)
                            MinY = float( MinY)
                            MaxX = float( MaxX)
                            MaxY = float( MaxY)
                            
                            # Make sure extent is within range
                            if MinX > fullExtent[ "xmin"] and MaxX < fullExtent[ "xmax"] and MinY > fullExtent[ "ymin"] and MaxY < fullExtent[ "ymax"]:
                                shapeArray.add( arcpy.Point( MinX, MinY))
                                shapeArray.add( arcpy.Point( MinX, MaxY))
                                shapeArray.add( arcpy.Point( MaxX, MaxY))
                                shapeArray.add( arcpy.Point( MaxX, MinY))
                                shapeArray.add( arcpy.Point( MinX, MinY))
                                polygonGeo = arcpy.Polygon(shapeArray)
                        
                        # Pick out Size
                        if key == "Size" and val.count( ",") == 1:
                            eventWidth, eventHeight = val.split( ",")
                            eventWidth = float( eventWidth)
                            eventHeight = float( eventHeight)
                        
                        # Pick out Scale
                        if key == "Scale":
                            eventScale = float( val)
                            eventInvScale = 1 / eventScale
                
                # Save if Shape created
                if shapeArray.count > 0:                    
                    
                    # Add Shape and Event Date
                    cursorFC.insertRow([polygonGeo, eventDateTime, eventScale, eventInvScale, eventWidth, eventHeight])             
                    
                    # Clear out Array points
                    shapeArray.removeAll()
                    
                    logEvents += 1
        if cursorFC:
            del cursorFC
            
        arcpy.AddMessage("Total number of events found in logs: {0}".format(logEvents))
        
        return
    

def getFullExtent( extentURL):
    #A function to query service for Extent and Spatial Reference details
        
    params = urllib.urlencode({'f': 'json'})     
    data = urllib2.urlopen(extentURL, params).read()
        
    if 'fullExtent' not in data:
        arcpy.AddError("Error returned by Service Query operation. " + str(data))
    else:   
        # Deserialize response into Python object
        dataObj = json.loads(data)    
        
        if not 'fullExtent' in dataObj:
            arcpy.AddError("Unable to find Extent detail for '{0}'!".format(extentURL))
        elif not 'spatialReference' in dataObj[ 'fullExtent']:
            arcpy.AddError( "Unable to find Spatial Reference for '{0}'!".format( extentURL))
        else:
            return dataObj['fullExtent']
    
    return


def createFC(outputFC, srid):
    #A function to create new Featureclass with required fields.  
    
    if arcpy.Exists(outputFC):
        arcpy.AddWarning("Output FC already exists, if overwrite data is not on this will fail.")
        #arcpy.Delete_management(outputFC)
    
    fc = arcpy.CreateFeatureclass_management(os.path.dirname(outputFC), os.path.basename(outputFC), "POLYGON", '', '', '', srid)
        
    arcpy.AddField_management(outputFC, "EventDate", "DATE", None, None, None, None, "NULLABLE", "NON_REQUIRED")
    arcpy.AddField_management(outputFC, "Scale", "DOUBLE", 19, 2, None, None, "NULLABLE", "NON_REQUIRED")
    arcpy.AddField_management(outputFC, "InvScale", "DOUBLE", 19, 12, None, None, "NULLABLE", "NON_REQUIRED")
    arcpy.AddField_management(outputFC, "Width", "LONG", 9, None, None, None, "NULLABLE", "NON_REQUIRED")
    arcpy.AddField_management(outputFC, "Height", "LONG", 9, None, None, None, "NULLABLE", "NON_REQUIRED")
    
    return fc
    
    
if __name__ == "__main__":     
    
    # Gather inputs      
    server = arcpy.GetParameterAsText(0) 
    port = arcpy.GetParameterAsText(1) 
    adminUser = arcpy.GetParameterAsText(2)     
    adminPass = arcpy.GetParameterAsText(3)     
    
    mapService = arcpy.GetParameterAsText(4) 
    outputFC = arcpy.GetParameterAsText(5)     
    
    
    makeFC_FromExtents(server, port, adminUser, adminPass, mapService, outputFC)