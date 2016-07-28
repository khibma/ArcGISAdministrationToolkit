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

import _commonFunctions
import arcpy
import os
import datetime



def makeFC_FromExtents(handler, mapService, outputFC):
    ''' Function to get all services
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.
    Note: Will not return any services in the Utilities or System folder
    '''

    extentURL = "{}/services/{}".format(handler.baseURL.replace("admin", "rest"), mapService.replace( ".", "/"))
    fullExtent = handler.url_request(extentURL, req_type='GET')

    if not 'fullExtent' in fullExtent.keys():
        arcpy.AddError("Unable to find Extent detail for '{0}'!".format(extentURL))
    elif not 'spatialReference' in fullExtent[ 'fullExtent']:
        arcpy.AddError( "Unable to find Spatial Reference for '{0}'!".format( extentURL))
    else:
        extent = fullExtent['fullExtent']


    logQuery_url = "{}/logs/query".format(handler.baseURL)
    logFilter = "{'services': ['" + mapService + "']}"
    params = {'level': 'FINE', 'filter': logFilter}
    extentData = handler.url_request(logQuery_url, params, req_type='POST')


    # Create a featureclass, and open a cursor
    fc = createFC( outputFC, extent[ "spatialReference"][ "wkid"])
    cursorFC = arcpy.da.InsertCursor(fc, ["SHAPE@", "EventDate", "Scale", "InvScale", "Width", "Height"])

    # Variable to track number of events found for ExportMapImage call
    logEvents = 0

    # Array to hold Shape
    shapeArray = arcpy.Array()

    # Iterate over messages
    for item in extentData["logMessages"]:
        eventDateTime = datetime.datetime.fromtimestamp( float( item["time"]) / 1000)

        if item["message"].startswith( "Extent:"):
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
                        if MinX > extent["xmin"] and MaxX < extent["xmax"] and \
                           MinY > extent["ymin"]  and MaxY < extent[ "ymax"]:
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


def createFC(outputFC, srid):
    #A function to create new Featureclass with required fields.

    if arcpy.Exists(outputFC):
        arcpy.AddWarning("Output FC already exists, if overwrite data is not on this will fail.")
        #arcpy.Delete_management(outputFC)

    fc = arcpy.CreateFeatureclass_management(os.path.dirname(outputFC),
                                             os.path.basename(outputFC), "POLYGON", '', '', '', srid)

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

    handler = _commonFunctions.connectionHelper(server, port, adminUser, adminPass)

    makeFC_FromExtents(handler, mapService, outputFC)