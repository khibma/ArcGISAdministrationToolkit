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

import _commonFunctions
import arcpy


def createFolder(handler, folderName, folderDescription):
    ''' Function to create a folder
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    folderName = String with a folder name
    folderDescription = String with a description for the folder
    '''

    folderProp_dict = { "folderName": folderName,
                        "description": folderDescription
                      }

    create_url = "{}/services/createFolder".format(handler.baseURL)
    status = handler.url_request(create_url, folderProp_dict, "POST")


    if 'success' in status.values():
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

    handler = _commonFunctions.connectionHelper(server, port, adminUser, adminPass)

    createFolder(handler, folderName, folderDescription)

